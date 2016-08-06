"""The main frame."""

import wx, application, showing
from threading import Thread
from six import string_types
from wxgoodies.keys import add_accelerator
from db import to_object, list_to_objects, session, Track, Playlist, Station, Artist
from config import save, system_config, interface_config, sections
from sqlalchemy import func, or_
from configobj_dialog import ConfigObjDialog
from gmusicapi.exceptions import NotLoggedIn
from functions.util import do_login, format_track, load_station
from functions.google import playlist_action, delete_station
from functions.sound import play, get_previous, get_next, set_volume, seek, seek_amount
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
  self.Bind(wx.EVT_MENU, self.on_previous, pm.Append(wx.ID_ANY, '&Previous Track\tCTRL+LEFT', 'Play the previous track.'))
  self.Bind(wx.EVT_MENU, self.on_next, pm.Append(wx.ID_ANY, '&Next Track\tCTRL+RIGHT', 'Play the next track.'))
  self.Bind(wx.EVT_MENU, lambda event: set_volume(max(0, self.volume.GetValue() - 5)), pm.Append(wx.ID_ANY, 'Volume &Down\tCTRL+DOWN', 'Reduce volume by 5%.'))
  self.Bind(wx.EVT_MENU, lambda event: set_volume(min(100, self.volume.GetValue() + 5)), pm.Append(wx.ID_ANY, 'Volume &Up\tCTRL+UP', 'Increase volume by 5%.'))
  mb.Append(pm, '&Play')
  sm = wx.Menu()
  self.Bind(wx.EVT_MENU, lambda event: Thread(target = self.load_library,).start(), sm.Append(wx.ID_ANY, '&Library\tCTRL+L', 'Load every song in your Google Music library.'))
  self.Bind(wx.EVT_MENU, lambda event: Thread(target = self.load_promoted_songs).start(), sm.Append(wx.ID_ANY, 'Promoted &Songs\tCTRL+P', 'Load promoted songs.'))
  self.Bind(wx.EVT_MENU, lambda event: self.add_results(self.queue, showing = showing.SHOWING_QUEUE), sm.Append(wx.ID_ANY, '&Queue\tCTRL+SHIFT+Q', 'Show all tracks in the play queue.'))
  self.Bind(wx.EVT_MENU, lambda event: self.add_results(session.query(Track).all(), showing = showing.SHOWING_CATALOGUE), sm.Append(wx.ID_ANY, '&Catalogue\tCTRL+0', 'Load all songs which are stored in the local database.'))
  self.playlists_menu = wx.Menu()
  self.Bind(wx.EVT_MENU, lambda event: Thread(target = playlist_action, args = ['Select a playlist to load', 'Playlists', lambda playlist: wx.CallAfter(self.add_results, playlist.tracks, showing = playlist)]).start(), self.playlists_menu.Append(wx.ID_ANY, '&Remote...\tCTRL+1', 'Load a playlist from google.'))
  self.Bind(wx.EVT_MENU, self.edit_playlist, self.playlists_menu.Append(wx.ID_ANY, '&Edit Playlist...\tCTRL+SHIFT+E', 'Edit or delete a playlist.'))
  sm.AppendSubMenu(self.playlists_menu, '&Playlists', 'Select ocal or a remote playlist to view.')
  self.stations_menu = wx.Menu()
  self.Bind(wx.EVT_MENU, self.load_remote_station, self.stations_menu.Append(wx.ID_ANY, '&Remote...\tCTRL+2', 'Load a readio station from Google.'))
  self.delete_stations_menu = wx.Menu()
  self.stations_menu.AppendSubMenu(self.delete_stations_menu, '&Delete')
  sm.AppendSubMenu(self.stations_menu, '&Radio Stations', 'Locally stored and remote radio stations.')
  mb.Append(sm, '&Source')
  self.options_menu = wx.Menu()
  for section in sections:
   self.Bind(wx.EVT_MENU, lambda event, section = section: ConfigObjDialog(section).Show(True), self.options_menu.Append(wx.ID_ANY, '&%s...' % section.title, 'Edit the %s configuration.' % section.title))
  self.Bind(wx.EVT_MENU, lambda event: AudioOptions(), self.options_menu.Append(wx.ID_ANY, '&Audio...\tF12', 'Configure advanced audio settings.'))
  mb.Append(self.options_menu, '&Options')
  self.SetMenuBar(mb)
  self.Bind(wx.EVT_SHOW, self.on_show)
  self.playlists = {} # A list of playlist: id key: value pairs.
  for p in session.query(Playlist).all():
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
  dlg = wx.SingleChoiceDialog(self, 'Select a playlist to edit', 'Edit Playlist', choices = [x.name for x in playlists])
  if dlg.ShowModal() == wx.ID_OK:
   EditPlaylistFrame(playlists[dlg.GetSelection()]).Show(True)
  dlg.Destroy()
 
 def on_show(self, event):
  """Show the window."""
  set_volume(system_config['volume'])
 
 def SetTitle(self, title = None):
  """Set the title to something."""
  if title is None:
   title = 'Not Playing'
  super(MainFrame, self).SetTitle('%s - %s' % (application.name, title))
 
 def load_result(self, result):
  """Load a result from a dictionary."""
  self.add_result(to_object(result))
 
 def add_result(self, result):
  """Add a result to the view."""
  self.view.Append(format_track(result))
  self.results.append(result)
 
 def load_results(self, results, *args, **kwargs):
  """Given a list of tracks results, load them into the database and then into add_results along with args and kwargs."""
  self.add_results(list_to_objects(results), *args, **kwargs)
 
 def add_results(self, results, clear = True, focus = True, showing = None):
  """Add results to the view."""
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
  self.status.SetStatusText('%s (%s %s)' % (text, len(self.results), 'song' if len(self.results) == 1 else 'songs'))
 
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
  application.running = False
  self.position_timer.Stop()
  if application.stream:
   application.stream.stop()
  system_config['offline_search'] = self.offline_search.IsChecked()
  system_config['volume'] = self.volume.GetValue()
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
    play(get_next(remove = True))
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
   dlg = wx.SingleChoiceDialog(self, 'Select a station to listen to', 'Radio Stations', choices = [x.name for x in stations])
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
 
 def do_delete_station(self, station):
  print(station.name)
