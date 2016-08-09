"""The main frame."""

import wx, application, showing
from threading import Thread
from random import shuffle
from six import string_types
from wxgoodies.keys import add_accelerator
from db import to_object, list_to_objects, session, Track, Playlist, Station, Artist
from config import save, system_config, interface_config, sections
from sqlalchemy import func, or_
from sqlalchemy.orm.exc import NoResultFound
from configobj_dialog import ConfigObjDialog
from gmusicapi.exceptions import NotLoggedIn
from accessibility import output
from functions.util import do_login, format_track, load_playlist, load_station
from functions.google import playlist_action, artist_action, delete_station, add_to_playlist, add_to_library, remove_from_library, load_artist_tracks, load_artist_top_tracks
from functions.sound import play, get_previous, get_next, set_volume, seek, seek_amount, queue
from .audio_options import AudioOptions
from .track_menu import TrackMenu
from .edit_playlist_frame import EditPlaylistFrame

SEARCH_LABEL = '&Find'
SEARCHING_LABEL = '&Searching...'
PLAY_LABEL = '&Play'
PAUSE_LABEL = '&Pause'

class MainFrame(wx.Frame):
 """The main frame."""
 def __init__(self, *args, **kwargs):
  super(MainFrame, self).__init__(*args, **kwargs)
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
  vs.Add(self.view, 1, wx.GROW)
  ls = wx.BoxSizer(wx.VERTICAL)
  ls.Add(wx.StaticText(p, label = '&Lyrics'), 0, wx.GROW)
  self.lyrics = wx.TextCtrl(p, style = wx.TE_MULTILINE | wx.TE_READONLY)
  ls.Add(self.lyrics, 1, wx.GROW)
  s2.AddMany([
   (vs, 1, wx.GROW),
   (ls, 1, wx.GROW),
  ])
  s3 = wx.BoxSizer(wx.HORIZONTAL)
  s3.Add(wx.StaticText(p, label = '&Volume'), 0, wx.GROW)
  self.volume = wx.Slider(p, value = system_config['volume'], style = wx.SL_VERTICAL)
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
  mb = wx.MenuBar()
  fm = wx.Menu() # File menu.
  self.offline_search = fm.AppendCheckItem(wx.ID_ANY, '&Offline Search', 'Search the local database rather than google')
  self.offline_search.Check(system_config['offline_search'])
  self.Bind(wx.EVT_MENU, lambda event: self.Close(True), fm.Append(wx.ID_EXIT, '&Quit', 'Exit the program.'))
  mb.Append(fm, '&File')
  pm = wx.Menu() # Play menu.
  self.Bind(wx.EVT_MENU, self.play_pause, pm.Append(wx.ID_ANY, '&Play / Pause', 'Play or pause the current track.'))
  self.Bind(wx.EVT_MENU, self.do_stop, pm.Append(wx.ID_ANY, '&Stop\tCTRL+.', 'Stop the currently playlist track.'))
  self.Bind(wx.EVT_MENU, lambda event: queue(self.self.get_result()) if self.get_result() is not None else wx.Bell(), pm.Append(wx.ID_ANY, '&Queue Item\tSHIFT+RETURN', 'Add the currently focused track to the play queue.'))
  self.Bind(wx.EVT_MENU, self.on_previous, pm.Append(wx.ID_ANY, '&Previous Track\tCTRL+LEFT', 'Play the previous track.'))
  self.Bind(wx.EVT_MENU, self.on_next, pm.Append(wx.ID_ANY, '&Next Track\tCTRL+RIGHT', 'Play the next track.'))
  self.Bind(wx.EVT_MENU, lambda event: set_volume(max(0, self.volume.GetValue() - 5)), pm.Append(wx.ID_ANY, 'Volume &Down\tCTRL+DOWN', 'Reduce volume by 5%.'))
  self.Bind(wx.EVT_MENU, lambda event: set_volume(min(100, self.volume.GetValue() + 5)), pm.Append(wx.ID_ANY, 'Volume &Up\tCTRL+UP', 'Increase volume by 5%.'))
  repeat_menu = wx.Menu()
  self.repeat_off = repeat_menu.AppendRadioItem(wx.ID_ANY, '&Off', 'No repeat.')
  self.repeat_track = repeat_menu.AppendRadioItem(wx.ID_ANY, '&Track', 'Repeat just the currently playlist track.')
  self.repeat_all = repeat_menu.AppendRadioItem(wx.ID_ANY, '&All', 'Repeat all.')
  [self.repeat_off, self.repeat_track, self.repeat_all][int(system_config['repeat'])].Check(True)
  pm.AppendSubMenu(repeat_menu, '&Repeat', 'Repeat options')
  add_accelerator(self, 'CTRL+R', self.cycle_repeat)
  self.Bind(wx.EVT_MENU, self.on_shuffle, pm.Append(wx.ID_ANY, '&Shuffle\tCTRL+H', 'Shuffle the current view.'))
  mb.Append(pm, '&Play')
  sm = wx.Menu()
  self.Bind(wx.EVT_MENU, lambda event: Thread(target = self.load_library,).start(), sm.Append(wx.ID_ANY, '&Library\tCTRL+L', 'Load every song in your Google Music library.'))
  self.Bind(wx.EVT_MENU, lambda event: Thread(target = self.load_promoted_songs).start(), sm.Append(wx.ID_ANY, 'Promoted &Songs\tCTRL+P', 'Load promoted songs.'))
  self.Bind(wx.EVT_MENU, lambda event: self.add_results(self.queue, showing = showing.SHOWING_QUEUE), sm.Append(wx.ID_ANY, '&Queue\tCTRL+SHIFT+Q', 'Show all tracks in the play queue.'))
  self.Bind(wx.EVT_MENU, lambda event: self.add_results(session.query(Track).all(), showing = showing.SHOWING_CATALOGUE), sm.Append(wx.ID_ANY, '&Catalogue\tCTRL+0', 'Load all songs which are stored in the local database.'))
  self.Bind(wx.EVT_MENU, lambda event: self.add_results([x for x in session.query(Track).all() if x.downloaded is True], showing = showing.SHOWING_DOWNLOADED), sm.Append(wx.ID_ANY, '&Downloaded\tCTRL+D', 'Show all downloaded tracks.'))
  self.playlists_menu = wx.Menu()
  self.Bind(wx.EVT_MENU, lambda event: playlist_action('Select a playlist to load', 'Playlists', lambda playlist: self.add_results(playlist.tracks, showing = playlist)) if self.playlist_action is None else wx.Bell(), self.playlists_menu.Append(wx.ID_ANY, '&Remote...\tCTRL+1', 'Load a playlist from google.'))
  self.Bind(wx.EVT_MENU, self.edit_playlist, self.playlists_menu.Append(wx.ID_ANY, '&Edit Playlist...\tCTRL+SHIFT+E', 'Edit or delete a playlist.'))
  sm.AppendSubMenu(self.playlists_menu, '&Playlists', 'Select ocal or a remote playlist to view.')
  self.stations_menu = wx.Menu()
  self.Bind(wx.EVT_MENU, self.load_remote_station, self.stations_menu.Append(wx.ID_ANY, '&Remote...\tCTRL+2', 'Load a readio station from Google.'))
  self.delete_stations_menu = wx.Menu()
  self.stations_menu.AppendSubMenu(self.delete_stations_menu, '&Delete')
  sm.AppendSubMenu(self.stations_menu, '&Radio Stations', 'Locally stored and remote radio stations.')
  mb.Append(sm, '&Source')
  tm = wx.Menu()
  self.Bind(wx.EVT_MENU, self.load_artist_tracks, tm.Append(wx.ID_ANY, 'Goto &Artist\tCTRL+$', 'View all tracks by the artist of the currently focused track.'))
  self.Bind(wx.EVT_MENU, self.load_top_tracks, tm.Append(wx.ID_ANY, '&Load Artist &Top Tracks', 'Load the top tracks for the artist of the currently selected result.'))
  self.Bind(wx.EVT_MENU, self.load_related_artist, tm.Append(wx.ID_ANY, 'Go To &Related Artist...\tCTRL+7', 'Select an artist related to the artist of the currently selected result.'))
  self.Bind(wx.EVT_MENU, self.load_album, tm.Append(wx.ID_ANY, 'Go To A&lbum\tCTRL+5', 'Load the album of the currently selected track.'))
  self.Bind(wx.EVT_MENU, self.load_top_tracks, tm.Append(wx.ID_ANY, '&Top Tracks\tCTRL+;', 'Load the top tracks for the artist of the currently selected track.'))
  self.Bind(wx.EVT_MENU, self.toggle_library, tm.Append(wx.ID_ANY, 'Add / Remove From &Library\tCTRL+/', 'Add or remove the currently selected track from library.'))
  self.Bind(wx.EVT_MENU, lambda event: playlist_action('Select a playlist to add this track to', 'Select A Playlist', add_to_playlist, self.get_result()) if self.get_result() is not None else wx.Bell(), tm.Append(wx.ID_ANY, 'Add To &Playlist...\tCTRL+8', 'Add the currently selected track to a playlist.'))
  self.Bind(wx.EVT_MENU, lambda event: add_to_playlist(self.last_playlist, self.get_result()) if self.last_playlist is not None and self.self.get_result() is not None else wx.Bell(), tm.Append(wx.ID_ANY, 'Add To Most Recent Playlist\tCTRL+RETURN', 'Add the currently selected track to the most recent playlist.'))
  mb.Append(tm, '&Track')
  self.options_menu = wx.Menu()
  for section in sections:
   self.Bind(wx.EVT_MENU, lambda event, section = section: ConfigObjDialog(section).Show(True), self.options_menu.Append(wx.ID_ANY, '&%s...' % section.title, 'Edit the %s configuration.' % section.title))
  self.Bind(wx.EVT_MENU, lambda event: AudioOptions(), self.options_menu.Append(wx.ID_ANY, '&Audio...\tF12', 'Configure advanced audio settings.'))
  mb.Append(self.options_menu, '&Options')
  self.SetMenuBar(mb)
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
  set_volume(system_config['volume'])
 
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
  self.status.SetStatusText(interface_config['status_format'].format(text, loaded, total, percentage))
 
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
    results = [x['track'] for x in application.api.search(what, max_results = interface_config['results'])['song_hits']]
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
  self.position_timer.Stop()
  if application.stream:
   application.stream.stop()
  if application.old_stream:
   application.old_stream.stop()
  system_config['offline_search'] = self.offline_search.IsChecked()
  system_config['volume'] = self.volume.GetValue()
  if self.repeat_track.IsChecked():
   system_config['repeat'] = '1'
  elif self.repeat_all.IsChecked():
   system_config['repeat'] = '2'
  else:
   system_config['repeat'] = '0'
  session.commit()
  save()
  event.Skip()
 
 def on_activate(self, event):
  """Enter was pressed on a track."""
  cr = self.view.GetSelection()
  if cr == -1:
   return wx.Bell()
  else:
   play(self.results[cr])
   if interface_config['clear_queue']:
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
   if pos == length:
    n = get_next(remove = True)
    if n is None:
     self.SetTitle()
    else:
     play(n)
  else:
   self.position.SetValue(0)
 
 def play_pause(self, event):
  """Play or pause the current track."""
  if application.stream:
   if application.stream.is_paused:
    application.stream.play()
    self.play.SetLabel(PAUSE_LABEL)
   else:
    application.stream.pause()
    self.play.SetLabel(PLAY_LABEL)
   self.SetTitle()
  else:
   wx.Bell()
 
 def on_context(self, event):
  """Context menu for tracks view."""
  cr = self.view.GetSelection()
  if cr == -1:
   wx.Bell()
  else:
   self.PopupMenu(TrackMenu(self.results[cr]), wx.GetMousePosition())
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
 
 def on_shuffle(self, event):
  """Shuffle tracks."""
  self.autoload = []
  shuffle(self.results)
  self.add_results(self.results)
   
 def load_album(self, event):
  cr = self.view.GetSelection()
  if cr == -1:
   wx.Bell()
  else:
   def f(track):
    """Load the album and show it."""
    try:
     album = application.api.get_album_info(track.album_id)
     wx.CallAfter(application.frame.add_results, album.get('tracks', []), showing = '%s - %s' % (track.artist, album.get('name', 'Unknown Album %s' % track.year)))
    except NotLoggedIn:
     do_login(callback = self.load_album)
   Thread(target = f, args = [self.results[cr]]).start()
 
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
   
  output.speak('Repeat %s.' % mode)
 
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
