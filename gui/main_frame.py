"""The main frame."""

import wx, application, showing, logging
from threading import Thread
from six import string_types
from wxgoodies.keys import add_accelerator
from datetime import timedelta
from db import to_object, list_to_objects, session, Track, Playlist, Station, Artist
from config import save, config
from sqlalchemy import func, or_
from sqlalchemy.orm.exc import NoResultFound
from gmusicapi.exceptions import NotLoggedIn
from lyricscraper.lyrics import Lyrics
from functions.network import get_lyrics
from functions.util import do_login, format_track, format_timedelta, load_playlist, load_station, clean_library
from functions.google import artist_action, delete_station, add_to_library, remove_from_library, load_artist_tracks, load_artist_top_tracks, album_action
from functions.sound import play, get_previous, get_next, set_volume, seek, seek_amount
from lyrics import LocalEngine
from .menus.context import ContextMenu
from .menus.main import MainMenu
from .edit_playlist_frame import EditPlaylistFrame

logger = logging.getLogger(__name__)
SEARCH_LABEL = '&Find'
SEARCHING_LABEL = '&Searching...'
PLAY_LABEL = '&Play'
PAUSE_LABEL = '&Pause'

class MainFrame(wx.Frame):
 """The main frame."""
 def __init__(self, *args, **kwargs):
  super(MainFrame, self).__init__(*args, **kwargs)
  self.played = [] # The tracks from the current view which have already been played.
  self.last_playlist = None # The playlist that most recently had a track added to it.
  self.playlist_action = None # An action to be called when all playlists have been localised.
  self.autoload = [] # Tracks to autoload in order.
  self.showing = None # Set it to the currently showing playlist or one of the showing.* constants from functions.sound.
  self.queue = [] # The play queue.
  self.results = []
  p = wx.Panel(self)
  s = wx.BoxSizer(wx.VERTICAL)
  s1 = wx.BoxSizer(wx.HORIZONTAL)
  self.previous = wx.Button(p, label = '&Previous')
  self.previous.Bind(wx.EVT_BUTTON, self.on_previous)
  self.play = wx.Button(p, label = PLAY_LABEL)
  self.play.Bind(wx.EVT_BUTTON, self.play_pause)
  self.next = wx.Button(p, label = '&Next')
  self.next.Bind(wx.EVT_BUTTON, self.on_next)
  self.search_label = wx.StaticText(p, label = SEARCH_LABEL)
  self.search = wx.TextCtrl(p, style = wx.TE_PROCESS_ENTER)
  self.search.Bind(wx.EVT_TEXT_ENTER, lambda event: self.do_local_search(self.search.GetValue()) if self.offline_search.IsChecked() else self.do_remote_search(self.search.GetValue()))
  s1.AddMany([
   (self.previous, 0, wx.GROW),
   (self.play, 0, wx.GROW),
   (self.next, 0, wx.GROW),
   (self.search_label, 0, wx.GROW),
   (self.search, 1, wx.GROW)
  ])
  s2 = wx.BoxSizer(wx.HORIZONTAL)
  vs = wx.BoxSizer(wx.VERTICAL)
  vs.Add(wx.StaticText(p, label = '&Tracks'), 0, wx.GROW)
  self.view = wx.ListBox(p)
  add_accelerator(self.view, 'RETURN', self.on_activate)
  add_accelerator(self.view, 'SPACE', self.play_pause)
  self.view.SetFocus()
  self.view.Bind(wx.EVT_CONTEXT_MENU, self.on_context)
  add_accelerator(self.view, 'SHIFT+F10', self.on_context)
  vs.Add(self.view, 1, wx.GROW)
  ls = wx.BoxSizer(wx.VERTICAL)
  ls.Add(wx.StaticText(p, label = '&Lyrics'), 0, wx.GROW)
  self.lyrics = wx.TextCtrl(p, value = 'Play a song to view lyrics.', style = wx.TE_MULTILINE | wx.TE_READONLY)
  ls.Add(self.lyrics, 1, wx.GROW)
  ls.Add(wx.StaticText(p, label = 'Artist &Biography'), 0, wx.GROW)
  self.artist_bio = wx.TextCtrl(p, style = wx.TE_MULTILINE | wx.TE_READONLY)
  ls.Add(self.artist_bio, 0, wx.GROW)
  s2.AddMany([
   (vs, 1, wx.GROW),
   (ls, 1, wx.GROW),
  ])
  s3 = wx.BoxSizer(wx.HORIZONTAL)
  s3.Add(wx.StaticText(p, label = '&Volume'), 0, wx.GROW)
  self.volume = wx.Slider(p, value = config.system['volume'], style = wx.SL_VERTICAL)
  self.volume.Bind(wx.EVT_SLIDER, lambda event: set_volume(self.volume.GetValue()))
  s3.Add(self.volume, 1, wx.GROW)
  s3.Add(wx.StaticText(p, label = '&Position'), 0, wx.GROW)
  self.position= wx.Slider(p, style = wx.SL_HORIZONTAL)
  self.position.Bind(wx.EVT_SLIDER, lambda event: application.stream.set_position((int(application.stream.get_length() / 100) * self.position.GetValue())) if application.stream else None)
  add_accelerator(self, 'SHIFT+LEFT', self.rewind)
  add_accelerator(self, 'SHIFT+RIGHT', self.fastforward)
  self.position_timer = wx.Timer(self)
  self.Bind(wx.EVT_TIMER, self.play_manager, self.position_timer)
  self.position_timer.Start(10)
  s.AddMany([
   (s1, 0, wx.GROW),
   (s2, 1, wx.GROW),
   (s3, 0, wx.GROW),
  ])
  p.SetSizerAndFit(s)
  self.SetTitle()
  self.Bind(wx.EVT_CLOSE, self.on_close)
  self.SetMenuBar(MainMenu(self))
  self.Bind(wx.EVT_SHOW, self.on_show)
  self.playlists = {} # A list of playlist: id key: value pairs.
  playlists = session.query(Playlist).order_by(Playlist.name).all()
  playlists.reverse()
  for p in playlists:
   self.add_playlist(p)
  self.stations = {} # The same as .playlists except for radio stations.
  for s in session.query(Station).all():
   self.add_station(s)
  self.status = self.CreateStatusBar()
  self.status.SetStatusText('Nothing playing yet')
 
 def add_playlist(self, playlist):
  """Add playlist to the menu."""
  if playlist not in self.playlists:
   id = wx.NewId()
   self.playlists[playlist] = id
   self.Bind(wx.EVT_MENU, lambda event, playlist = playlist: self.add_results(playlist.tracks, showing = playlist), self.playlists_menu.Insert(0, id, '&%s' % playlist.name, playlist.description))
   return True
  else:
   return False
 
 def add_station(self, station):
  """Add playlist to the menu."""
  if station not in self.stations:
   id = wx.NewId()
   delete_id = wx.NewId()
   self.stations[station] = [id, delete_id]
   self.Bind(wx.EVT_MENU, lambda event, station = station: self.load_station(station), self.stations_menu.Insert(0, id, '&%s' % station.name, 'Load the %s station.' % station.name))
   self.Bind(wx.EVT_MENU, lambda event, station = station: delete_station(station) if wx.MessageBox('Are you sure you want to delete the %s station?' % station.name, 'Are You Sure?', style = wx.ICON_QUESTION | wx.YES_NO) == wx.YES else None, self.delete_stations_menu.Insert(0, delete_id, '&%s' % station.name, 'Delete the %s station' % station.name))
   return True
  else:
   return False
 
 def edit_playlist(self, event):
  """Delete a playlist from the local database."""
  playlists = list(self.playlists.keys())
  dlg = wx.SingleChoiceDialog(self, 'Select a playlist to edit', 'Edit Playlist', [x.name for x in playlists])
  if dlg.ShowModal() == wx.ID_OK:
   EditPlaylistFrame(playlists[dlg.GetSelection()]).Show(True)
  dlg.Destroy()
 
 def on_show(self, event):
  """Show the window."""
  set_volume(config.system['volume'])
 
 def SetTitle(self):
  """Set the title to something."""
  if application.stream is None:
   title = 'Not Playing'
   mode = None
  else:
   title = str(application.track)
   if application.stream.is_stopped:
    mode = 'Stopped'
   elif application.stream.is_paused:
    mode = 'Paused'
   else:
    mode = 'Playing'
  super(MainFrame, self).SetTitle('%s - %s%s' % (application.name, title, ' [{}]'.format(mode) if mode is not None else ''))
 
 def load_result(self, result):
  """Load a result from a dictionary."""
  self.add_result(to_object(result))
 
 def add_result(self, result):
  """Add a result to the view."""
  self.view.Append(format_track(result))
  self.results.append(result)
  if self.view.GetSelection() == -1:
   self.view.SetSelection(0)
 
 def load_results(self, results, *args, **kwargs):
  """Given a list of tracks results, load them into the database and then into add_results along with args and kwargs."""
  self.add_results(list_to_objects(results), *args, **kwargs)
 
 def add_results(self, results, clear = True, focus = True, showing = None):
  """Add results to the view."""
  if showing is None:
   showing = self.showing
  self.showing = showing
  if clear:
   self.played = [] # Clear the played tracks queue.
   self.view.Clear()
   self.results = []
   self.autoload = []
  for r in results:
   self.autoload.append(r)
  if focus:
   self.view.SetFocus()
  if clear:
   self.update_labels()
 
 def remove_result(self, result):
  """Remove a result given as a Track object or an integer."""
  if isinstance(result, Track):
   pos = self.results.index(result)
   self.view.Delete(pos)
   del self.results[pos]
  elif isinstance(result, int):
   self.view.Delete(result)
   del self.results[result]
  else:
   return TypeError('result must be given as either a Track object or an integer.')
 
 def update_status(self):
  """Update the text on the status bar."""
  if isinstance(self.showing, string_types):
   text = self.showing
  elif isinstance(self.showing, Playlist):
   text = 'Playlist: %s' % self.showing.name
  elif isinstance(self.showing, Station):
   text = 'Radio Station: %s' % self.showing.name
  elif isinstance(self.showing, Artist):
   text = 'Artist: %s' % self.showing
  else:
   text = 'Unknown [%s]' % self.showing
  loaded = len(self.results)
  total = len(self.results) + len(self.autoload)
  percentage = '%.2f' % (100 / total * loaded)
  duration = timedelta()
  for r in self.results:
   duration += r.duration
  self.status.SetStatusText(
   config.interface['status_bar_format'].format(
    text = text,
    loaded = loaded,
    total = total,
    percentage = percentage,
    duration = format_timedelta(duration)
   )
  )
 
 def load_library(self):
  """Load all the songs from the Google Music library."""
  try:
   lib = application.api.get_all_songs()
   wx.CallAfter(self.add_results, lib, showing = showing.SHOWING_LIBRARY)
  except NotLoggedIn:
   do_login(callback = self.load_library)
 
 def load_promoted_songs(self):
  """Load promoted songs from Google."""
  try:
   songs = application.api.get_promoted_songs()
   wx.CallAfter(self.load_results, songs, showing = showing.SHOWING_PROMOTED)
  except NotLoggedIn:
   do_login(callback = self.load_promoted_songs)
 
 def do_remote_search(self, what):
  """Perform a searchon Google Play Music for what."""
  def f(what):
   """Get the results and pass them onto f2."""
   try:
    results = [x['track'] for x in application.api.search(what, max_results = config.interface['results'])['song_hits']]
    def f2(results):
     """Clear the search box and change it's label back to search_label."""
     if results:
      self.search.Clear()
     self.load_results(results, showing = showing.SHOWING_SEARCH_REMOTE)
     self.search_label.SetLabel(SEARCH_LABEL)
   except NotLoggedIn:
    def f2(results):
     """Get the user to login."""
     self.search_label.SetLabel(SEARCH_LABEL)
     do_login(callback = f, args = [what])
    results = []
   wx.CallAfter(f2, results)
  self.search_label.SetLabel(SEARCHING_LABEL)
  Thread(target = f, args = [what]).start()
 
 def do_local_search(self, what):
  """Perform a local search for what."""
  what = '%%%s%%' % self.search.GetValue()
  results = session.query(Track).filter(
   or_(
    func.lower(Track.title).like(what),
    func.lower(Track.artist).like(what),
    func.lower(Track.album).like(what)
   )
  ).all()
  self.add_results(results, showing = showing.SHOWING_SEARCH_LOCAL)
 
 def on_close(self, event):
  """Close the window."""
  event.Skip()
  logger.info('Main frame closed.')
  self.position_timer.Stop()
  logger.info('Stopped the main timer.')
  if application.stream:
   application.stream.stop()
   logger.info('Stopped the currently playing stream.')
  else:
   logger.info('No track to stop.')
  logger.info('Updating configuration...')
  config.system['stop_after'] = self.stop_after.IsChecked()
  config.system['shuffle'] = self.shuffle.IsChecked()
  config.system['offline_search'] = self.offline_search.IsChecked()
  config.system['volume'] = self.volume.GetValue()
  if self.repeat_track.IsChecked():
   config.system['repeat'] = 1
  elif self.repeat_all.IsChecked():
   config.system['repeat'] = 2
  else:
   config.system['repeat'] = 0
  logger.info('Running session.commit.')
  session.commit()
  logger.info('Dumping configuration to disk.')
  save()
  logger.info('Cleaning the media directory.')
  clean_library()
 
 def on_activate(self, event):
  """Enter was pressed on a track."""
  res = self.get_result()
  if res is None:
   wx.Bell()
  else:
   play(res)
   if config.interface['clear_queue']:
    self.queue = []
 
 def update_labels(self):
  """Update the labels of the previous and next buttons."""
  prev = get_previous()
  self.previous.SetLabel('&Previous' if prev is None else '&Previous (%s)' % prev)
  next = get_next(remove = False)
  self.next.SetLabel('&Next' if next is None else '&Next (%s)' % next)
 
 def play_manager(self, event):
  """Manage the currently playing track."""
  try:
   load_playlist(self.playlist_action.playlists.pop(0))
  except AttributeError: # There is either no playlist action, or there are no playlists to load yet.
   pass
  except IndexError: # There are no more playlists. Let's rock!
   a = self.playlist_action
   self.playlist_action = None
   a.complete()
  if self.autoload:
   t = self.autoload.pop(0)
   if isinstance(t, dict):
    self.load_result(t)
   else:
    self.add_result(t)
   self.update_status()
  if application.stream:
   pos = application.stream.get_position()
   length = application.stream.get_length()
   if not self.position.HasFocus():
    self.position.SetValue(int(pos * (100 / length)))
   stop_after = self.stop_after.IsChecked()
   if (length - pos) <= (0 if stop_after else config.sound['fadeout_threshold']):
    if stop_after:
     n = None
    else:
     n = get_next(remove = True)
    play(n)
  else:
   self.position.SetValue(0)
 
 def play_pause(self, event):
  """Play or pause the current track."""
  if application.stream:
   if application.stream.is_paused or application.stream.is_stopped:
    application.stream.play(application.stream.is_stopped)
    self.play.SetLabel(PAUSE_LABEL)
   else:
    application.stream.pause()
    self.play.SetLabel(PLAY_LABEL)
   self.SetTitle()
  else:
   wx.Bell()
 
 def on_context(self, event):
  """Context menu for tracks view."""
  res = self.get_result()
  if res is None:
   wx.Bell()
  else:
   self.PopupMenu(ContextMenu(res), wx.GetMousePosition())
  event.Skip()
 
 def on_previous(self, event):
  """Play the previous track."""
  t = get_previous()
  if t:
   play(t)
  else:
   wx.Bell()
 
 def on_next(self, event):
  """Play the next track."""
  t = get_next(remove = True)
  if t:
   if application.stream:
    play(t)
  else:
   wx.Bell()
 
 def rewind(self, event):
  """Rewind the current track."""
  if application.stream:
   seek(seek_amount * -1)
  else:
   wx.Bell()
 
 def fastforward(self, event):
  """Fastforward the currently playing stream."""
  if application.stream:
   seek(seek_amount)
  else:
   wx.Bell()
 
 def load_remote_station(self, event):
  """Load a station from google."""
  try:
   data = application.api.get_all_stations()
   stations = []
   for d in data:
    stations.append(load_station(d))
   dlg = wx.SingleChoiceDialog(self, 'Select a station to listen to', 'Radio Stations', [x.name for x in stations])
   if dlg.ShowModal() == wx.ID_OK:
    Thread(target = self.load_station, args = [stations[dlg.GetSelection()]]).start()
   dlg.Destroy()
  except NotLoggedIn:
   do_login(callback = self.load_remote_station, args = [event])
 
 def load_station(self, station):
  """Load a station's tracks."""
  try:
   wx.CallAfter(self.add_results, application.api.get_station_tracks(station.id), showing = station)
  except NotLoggedIn:
   do_login(callback = self.load_station, args = [station])
 
 def load_current_album(self, event):
  """Load the album of the currently focused result."""
  res = self.get_result()
  if res is None:
   wx.Bell()
  else:
   def f(track):
    """Load the album and show it."""
    try:
     album = application.api.get_album_info(track.album_id)
     wx.CallAfter(application.frame.add_results, album.get('tracks', []), showing = '%s - %s' % (track.artist, album.get('name', 'Unknown Album %s' % track.year)))
    except NotLoggedIn:
     do_login(callback = f, args = [track])
   Thread(target = f, args = [res]).start()
 
 def get_result(self):
  """Return the currently focused result."""
  if self.view.GetSelection() != -1:
   return self.results[self.view.GetSelection()]
 
 def load_artist_tracks(self, event):
  """Load the tracks for the currently focused result."""
  res = self.get_result()
  if res is None:
   wx.Bell()
  else:
   artist_action(res.artists, load_artist_tracks)
 
 def load_top_tracks(self, event):
  """Load the top tracks for the artist of the currently selected track."""
  res = self.get_result()
  if res is None:
   wx.Bell()
  else:
   artist_action(res.artists, load_artist_top_tracks)
 
 def load_related_artist(self, event):
  """Load the tracks of a related artist."""
  def f1(artist):
   """Load the related artists and build the dialog."""
   try:
    a = application.api.get_artist_info(artist.id)
    wx.CallAfter(f2, a.get('related_artists', []))
   except NotLoggedIn:
    wx.CallAfter(do_login, callback = f1, args = [artist])
  def f2(artists):
   """Run through artists and add them to the database before building the dialog."""
   results = [] # The list of Artist objects.
   for a in artists:
    try:
     artist = session.query(Artist).filter(Artist.id == a['artistId']).one()
    except NoResultFound:
     artist = Artist(id = a['artistId'])
    artist.populate(a)
    session.add(artist)
    results.append(artist)
   session.commit()
   dlg = wx.SingleChoiceDialog(self, 'Select a related artist', 'Related Artists', [x.name for x in results])
   if dlg.ShowModal() == wx.ID_OK:
    res = results[dlg.GetSelection()]
   else:
    res = None
   dlg.Destroy()
   if res is not None:
    artist_action([res], load_artist_top_tracks)
  res = self.get_result()
  if res is None:
   wx.Bell()
  else:
   artist_action(res.artists, f1)
 
 def cycle_repeat(self, event):
  """Cycle through repeat modes."""
  if self.repeat_off.IsChecked():
   self.repeat_track.Check(True)
   mode = 'track'
  elif self.repeat_track.IsChecked():
   self.repeat_all.Check(True)
   mode = 'all'
  else:
   self.repeat_off.Check(True)
   mode = 'off'
  logger.info('Set repeat mode to %s.' % mode)
 
 def do_stop(self, event):
  """Stop the currently playing track."""
  if application.stream:
   application.stream.stop()
   self.SetTitle()
   application.stream.set_position(0)
  else:
   wx.Bell()
 
 def toggle_library(self, event):
  """Add or remove the currently selected track from the library."""
  res = self.get_result()
  if res is None:
   wx.Bell()
  else:
   if res.in_library:
    if wx.MessageBox('Remove %s from your library?' % res, 'Are You Sure', style = wx.ICON_QUESTION | wx.YES_NO) == wx.YES:
     remove_from_library(res)
   else:
    add_to_library(res)
    wx.MessageBox('%s was added to your library.' % res, 'Added')
 
 def load_album(self, event):
  """Load an album from the currently selected artist."""
  do_login()
  def f(id):
   """Get the album and load it from it's ID."""
   album = application.api.get_album_info(id)
   wx.CallAfter(self.add_results, album.get('tracks', []), showing = '%s - %s' % (album.get('artist', 'Unknown Artist'), album.get('name', 'Unknown Album %s' % album['year'])))
  res = self.get_result()
  if res is None:
   wx.Bell()
  else:
   artist_action(res.artists, lambda artist: album_action(artist, f))
 
 def select_playing(self, event):
  """Select the currently playing track."""
  res = application.track
  if res is None:
   return wx.Bell()
  elif res in self.results:
   self.view.SetSelection(self.results.index(res))
  else:
   self.add_results([res], showing = 'Currently Playing Track')
  self.view.SetFocus()
 
 def update_lyrics(self, track):
  """Update the lyrics view."""
  def f(track, lyrics):
   """Do the actual updating."""
   if lyrics is not None:
    logger.info('Found lyrics using the %s engine.', lyrics.engine.name)
    track.lyrics = lyrics.lyrics
    session.add(track)
    session.commit()
    value = '{0.artist} - {0.title} ({0.engine.name})\n\n{0.lyrics}'.format(lyrics)
   else:
    if config.storage['lyrics']:
     value = 'No lyrics found for {artist} - {title}.'.format(artist = track.artist, title = track.title)
    else:
     value = ''
   self.lyrics.SetValue(value)
   if track.artists[0].bio is not None:
    self.artist_bio.SetValue(track.artists[0].bio.strip())
   else:
    self.artist_bio.Clear()
  if track.lyrics is None:
   if config.storage['lyrics']:
    try:
     lyrics = get_lyrics(track)
    except ValueError:
     lyrics = None # No lyrics found.
   else:
    lyrics = None
  else:
   lyrics = Lyrics(track.artist, track.title, track.lyrics, LocalEngine())
  wx.CallAfter(f, track, lyrics)
