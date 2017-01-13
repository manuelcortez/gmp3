"""The main frame."""

import wx, application, showing, logging, sys, pyperclip
from threading import Thread
from functools import partial
from six import string_types
from wxgoodies.keys import add_accelerator, add_hotkey
from datetime import timedelta
from server import tracks
from db import to_object, list_to_objects, session, Track, Playlist, Station, Artist
from config import save, config
from sqlalchemy import func, or_
from sqlalchemy.orm.exc import NoResultFound
from gmusicapi.exceptions import NotLoggedIn
from sound_lib.main import BassError
from lyricscraper.lyrics import Lyrics
from functions.network import get_lyrics
from functions.util import do_login, do_error, format_track, format_timedelta, load_playlist, load_station, clean_library
from functions.google import artist_action, add_to_library, remove_from_library, load_artist_tracks, load_artist_top_tracks, album_action, remove_from_playlist
from functions.sound import play, get_previous, get_next, set_volume, seek, seek_amount
from lyrics import LocalEngine
from .menus.context import ContextMenu
from .edit_playlist_frame import EditPlaylistFrame
from .lyrics_frame import LyricsFrame

logger = logging.getLogger(__name__)
SEARCH_LABEL = '&Find'
SEARCHING_LABEL = '&Searching...'
PLAY_LABEL = 'Play'
PAUSE_LABEL = 'Pause'

class MainFrame(wx.Frame):
 """The main frame."""
 def __init__(self, *args, **kwargs):
  self.commands = [] # Commands to be executed from the context menu.
  self.initialised = False # Set to True when everything's done.
  super(MainFrame, self).__init__(*args, **kwargs)
  try:
   add_hotkey(self, 'MEDIA_PLAY_PAUSE', self.play_pause)
   add_hotkey(self, 'MEDIA_PREV_TRACK', self.on_previous)
   add_hotkey(self, 'MEDIA_NEXT_TRACK', self.on_next)
  except RuntimeError:
   logger.warning('Media keys will not be available because no win32con found.')
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
  self.menu = wx.Button(p, label = '&Menu')
  self.search_label = wx.StaticText(p, label = SEARCH_LABEL)
  self.search = wx.TextCtrl(p, style = wx.TE_PROCESS_ENTER)
  self.search.Bind(wx.EVT_TEXT_ENTER, lambda event: self.do_local_search(self.search.GetValue()) if self.offline_search.IsChecked() else self.do_remote_search(self.search.GetValue()))
  s1.AddMany([
   (self.previous, 0, wx.GROW),
   (self.play, 0, wx.GROW),
   (self.next, 0, wx.GROW),
   (self.menu, 0, wx.GROW),
   (self.search_label, 0, wx.GROW),
   (self.search, 1, wx.GROW)
  ])
  s2 = wx.BoxSizer(wx.HORIZONTAL)
  vs = wx.BoxSizer(wx.VERTICAL)
  vs.Add(wx.StaticText(p, label = '&Tracks'), 0, wx.GROW)
  self.view = wx.ListBox(p)
  add_accelerator(self.view, 'RETURN', self.on_activate)
  self.view.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_activate)
  add_accelerator(self.view, 'SPACE', self.play_pause)
  self.view.Bind(wx.EVT_LISTBOX_DCLICK, self.on_activate)
  self.view.SetFocus()
  self.view.Bind(wx.EVT_CONTEXT_MENU, self.on_context)
  if sys.platform == 'darwin':
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
  self.position_timer.Start(50)
  s.AddMany([
   (s1, 0, wx.GROW),
   (s2, 1, wx.GROW),
   (s3, 0, wx.GROW),
  ])
  p.SetSizerAndFit(s)
  self.SetTitle()
  self.Bind(wx.EVT_CLOSE, self.on_close)
  self.Bind(wx.EVT_SHOW, self.on_show)
  self.playlists = {} # A list of playlist: id key: value pairs.
  self.stations = {} # The same as .playlists except for radio stations.
  self.status = self.CreateStatusBar()
  self.status.SetStatusText('Nothing playing yet')
  add_accelerator(self, 'CTRL+R', self.cycle_repeat)

 def add_playlist(self, playlist):
  """Add playlist to the menu."""
  if playlist not in self.playlists:
   tracks.storage.playlists.append(
    {
     'key': playlist.key,
     'name': playlist.name,
     'description': playlist.description
    }
   )
   id = wx.NewId()
   self.playlists[playlist] = id
   self.playlists_menu.add_playlist(playlist, id = id)
   logger.info('Adding playlist %s with id %s.', playlist.name, id)
   return True
  else:
   logger.info('Playlist %s already had an id of %s.', playlist.name, self.playlists[playlist])
   return False

 def add_station(self, station):
  """Add station to the menu."""
  if station not in self.stations:
   tracks.storage.stations.append(
    {
     'key': station.key,
     'name': station.name
    }
   )
   id = wx.NewId()
   delete_id = wx.NewId()
   self.stations[station] = [id, delete_id]
   self.stations_menu.add_station(station, id = id, delete_id = delete_id)
   logger.info('Adding station %s with an id of %s and a delete id of %s.', station.name, *self.stations[station])
   return True
  else:
   logger.info('Station %s already has an id of %s and a delete id of %s.', station.name, *self.stations[station])
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
  if not self.initialised:
   from .menus.main import MainMenu
   from .menus.playlists import PlaylistsMenu
   from .menus.stations import StationsMenu
   from .menus.taskbar import TaskBarMenu
   self.menu.Bind(wx.EVT_BUTTON, lambda event: self.PopupMenu(TaskBarMenu(self), wx.GetMousePosition()))
   from .taskbar import TaskBarIcon, FakeTaskBarIcon
   try:
    self.tb_icon = TaskBarIcon()
   except SystemError as e:
    self.tb_icon = FakeTaskBarIcon()
    logger.warning('Creating the taskbar icon caused an errorL')
    logger.exception(e)
   self.playlists_menu = PlaylistsMenu(self, add_playlists = False)
   self.stations_menu = StationsMenu(self, add_stations = False)
   self.delete_stations_menu = self.stations_menu.delete_menu
   self.SetMenuBar(MainMenu(self))
   for p in session.query(Playlist).order_by(Playlist.name.desc()).all():
    self.add_playlist(p)
   for s in session.query(Station).order_by(Station.name.desc()).all():
    self.add_station(s)
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
  title = '%s%s' % (title, ' [{}]'.format(mode) if mode is not None else '')
  tracks.storage.now_playing = title
  tracks.storage.previous = get_previous()
  if tracks.storage.previous is None:
   tracks.storage.previous = 'No Track'
  else:
   tracks.storage.previous = str(tracks.storage.previous)
  tracks.storage.next = get_next(remove = False)
  if tracks.storage.next is None:
   tracks.storage.next = 'No Track'
  else:
   tracks.storage.next = str(tracks.storage.next)
  super(MainFrame, self).SetTitle('%s - %s' % (application.name, title))

 def load_result(self, result):
  """Load a result from a dictionary."""
  self.add_result(to_object(result))

 def add_result(self, result):
  """Add a result to the view."""
  session.add(result)
  session.commit()
  result_str = format_track(result)
  tracks.storage.tracks.append(
   {
    'key': result.key,
    'name': result_str
   }
  )
  self.view.Append(result_str)
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
   self.view.Clear()
   for thing in [
    self.played,
    self.results,
    tracks.storage.tracks,
    self.autoload
   ]:
    thing.clear()
  for r in results:
   self.autoload.append(r)
  if focus:
   self.view.SetFocus()
  if clear:
   self.update_labels()

 def remove_result(self, result):
  """Remove a result given as a Track object or an integer."""
  if isinstance(result, Track):
   if result in tracks.storage.tracks:
    tracks.storage.tracks.remove(result)
   try:
    pos = self.results.index(result)
    self.view.Delete(pos)
    del self.results[pos]
   except IndexError:
    pass # result not in self.results.
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
   wx.CallAfter(do_login, callback = self.load_library)

 def load_promoted_songs(self):
  """Load promoted songs from Google."""
  try:
   songs = application.api.get_promoted_songs()
   wx.CallAfter(self.load_results, songs, showing = showing.SHOWING_PROMOTED)
  except NotLoggedIn:
   wx.CallAfter(do_login, callback = self.load_promoted_songs)

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
  self.tb_icon.Destroy()
  event.Skip()
  logger.info('Main frame closed.')
  self.position_timer.Stop()
  logger.info('Stopped the main timer.')
  if application.stream:
   application.stream.stop()
   logger.info('Stopped the currently playing stream.')
  else:
   logger.info('No track to stop.')
  logger.info('Running session.commit.')
  session.commit()
  logger.info('Dumping configuration to disk.')
  save()
  logger.info('Cleaning the media directory.')
  clean_library()
  logger.info('Library cleaned.')

 def on_activate(self, event):
  """Enter was pressed on a track."""
  res = self.get_result()
  if res is None:
   wx.Bell()
  else:
   try:
    play(res)
   except BassError as e:
    do_error(e)
   if config.interface['clear_queue']:
    self.queue = []

 def update_labels(self):
  """Update the labels of the previous and next buttons."""
  prev = get_previous()
  prev = 'Previous' if prev is None else 'Previous (%s)' % prev
  self.previous.SetLabel('&%s' % prev)
  tracks.storage.previous = prev
  next = get_next(remove = False)
  next = 'Next' if next is None else 'Next (%s)' % next
  self.next.SetLabel('&%s' % next)
  tracks.storage.next = next
  if application.stream and application.stream.is_playing:
   pp = PAUSE_LABEL
  else:
   pp = PLAY_LABEL
  tracks.storage.play_pause = pp
  self.play.SetLabel('&' + pp)

 def play_manager(self, event):
  """Manage the currently playing track."""
  while self.commands:
   cmd = self.commands.pop()
   logger.info('Calling command %s.', cmd)
   try:
    wx.CallAfter(cmd)
   except Exception as e:
    logger.exception(e)
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
   try:
    pos = application.stream.get_position()
   except AssertionError:
    pos = 0.0
   length = application.stream.get_length()
   if not self.position.HasFocus() and length:
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
   else:
    application.stream.pause()
   self.update_labels()
   self.SetTitle()
  else:
   wx.Bell()

 def on_context(self, event):
  """Context menu for tracks view."""
  res = self.get_result()
  if res is None:
   wx.Bell()
  else:
   menu = ContextMenu(res)
   self.PopupMenu(menu, wx.GetMousePosition())
   menu.Destroy()

 def on_previous(self, event):
  """Play the previous track."""
  play(get_previous())

 def on_next(self, event):
  """Play the next track."""
  play(get_next(remove = True))

 def rewind(self, event):
  """Rewind the current track."""
  if self.view.HasFocus():
   if application.stream:
    seek(seek_amount * -1)
   else:
    wx.Bell()
  else:
   event.Skip()

 def fastforward(self, event):
  """Fastforward the currently playing stream."""
  if self.view.HasFocus():
   if application.stream:
    seek(seek_amount)
   else:
    wx.Bell()
  else:
   event.Skip()

 def load_remote_station(self, event):
  """Load a station from google."""
  try:
   data = application.api.get_all_stations()
   stations = []
   for d in data:
    stations.append(load_station(d))
   if not session.query(Station).filter(Station.id == 'IFL').count():
    stations.append(load_station(dict(name = 'I\'m Feeling Lucky', id = 'IFL')))
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
   def f(id):
    """Load the album and show it."""
    try:
     album = application.api.get_album_info(id)
     wx.CallAfter(self.add_results, album.get('tracks', []), showing = '%s - %s' % (album.get('artist', 'Unknown Artist'), album.get('name', 'Unknown Album %s' % album.get('year'))))
    except NotLoggedIn:
     do_login(callback = f, args = [id])
   Thread(target = f, args = [res.album_id]).start()

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
   if not results:
    return do_error('There are no related artists.')
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
   value = 1
  elif self.repeat_track.IsChecked():
   self.repeat_all.Check(True)
   mode = 'all'
   value = 2
  else:
   self.repeat_off.Check(True)
   mode = 'off'
   value = 0
  config.system['repeat'] = value
  logger.info('Set repeat mode to %s.' % mode)
  self.tb_icon.notify('Repeat %s.' % mode)

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
   if track is application.track: # Don't update for the wrong song.
    self.lyrics.SetValue(value)
   if track.artists[0].bio is not None:
    self.artist_bio.SetValue(track.artists[0].bio.strip())
   else:
    self.artist_bio.Clear()
  if track is not None and track.lyrics is None:
   if config.storage['lyrics']:
    try:
     lyrics = get_lyrics(track)
    except ValueError:
     lyrics = None # No lyrics found.
   else:
    lyrics = None
  else:
   if track is not None:
    lyrics = Lyrics(track.artist, track.title, track.lyrics, LocalEngine())
   else:
    lyrics = None
  if track is not None:
   wx.CallAfter(f, track, lyrics)

 def do_delete(self, event):
  """Delete the current result from the current view."""
  res = self.get_result()
  if not self.view.HasFocus():
   event.Skip()
  elif res is None:
   return wx.Bell()
  elif self.showing is showing.SHOWING_LIBRARY:
   if wx.MessageBox('Are you sure you want to delete %s from your library?' % res, 'Are You Sure', style = wx.ICON_QUESTION | wx.YES_NO) == wx.YES:
    remove_from_library(res)
  elif isinstance(self.showing, Playlist):
   for entry in res.playlist_entries:
    if entry.playlist is self.showing:
     if wx.MessageBox('Are you sure you want to remove %s from the %s playlist?' % (res, self.showing.name), 'Are You Sure', style = wx.ICON_QUESTION | wx.YES_NO) == wx.YES:
      remove_from_playlist(entry)
     break
   else:
    do_error('Cannot find %s in the %s playlist.' % (res, self.showing.name))
  else:
   do_error('No way to delete %s from the current view.' % res)

 def do_copy_id(self, track):
  """Copy the ID of the current track to the clipboard."""
  pyperclip.copy(track.id)

 def add_command(self, callback, *args, **kwargs):
  """Add a command to be called by play_manager."""
  self.commands.append(partial(callback, *args, **kwargs))

 def edit_lyrics(self, event):
  """Edit the lyrics for the currently-playing track."""
  res = self.get_result()
  if res is None:
   wx.Bell()
  else:
   LyricsFrame(res)
