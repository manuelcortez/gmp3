"""File menu."""

import application, wx
from time import ctime
from .base import BaseMenu
from config import system_config
from ..create_playlist import CreatePlaylist
from ..genre_station import GenreStation
from functions.google import create_station, artist_action

class FileMenu(BaseMenu):
 """The file menu."""
 def __init__(self, frame):
  self.name = '&File'
  self.frame = frame
  super(FileMenu, self).__init__()
  frame.Bind(wx.EVT_MENU, lambda event: CreatePlaylist().Show(True), self.Append(wx.ID_ANY, '&New Playlist...\tCTRL+N', 'Create a new playlist.'))
  frame.Bind(wx.EVT_MENU, lambda event: CreatePlaylist(name = 'Search Results From %s' % ctime(), tracks = frame.results).Show(True) if frame.results else wx.Bell(), self.Append(wx.ID_ANY, 'New &Playlist From Results...\tCTRL+SHIFT+N', 'Create a playlist from the currently showing results.'))
  self.AppendSeparator()
  stations_menu = wx.Menu()
  frame.Bind(wx.EVT_MENU, self.station_from_result, stations_menu.Append(wx.ID_ANY, 'From &Result...\tCTRL+9', 'Create a radio station based on the currently focused result.'))
  frame.Bind(wx.EVT_MENU, self.station_from_artist, stations_menu.Append(wx.ID_ANY, 'From &Artist...\tCTRL+SHIFT+4', 'Create a radio station based on the artist of the currently selected result.'))
  frame.Bind(wx.EVT_MENU, self.station_from_album, stations_menu.Append(wx.ID_ANY, 'From A&lbum...\tCTRL+SHIFT+5', 'Create a radio station from the album of the currently focused result.'))
  frame.Bind(wx.EVT_MENU, lambda event: GenreStation().Show(True), stations_menu.Append(wx.ID_ANY, 'From &Genre...\tCTRL+SHIFT+9', 'Create a radio station from a genre.'))
  self.AppendSubMenu(stations_menu, 'Create &Station...', 'Create a radio station from a number of sources.')
  self.AppendSeparator()
  frame.offline_search = self.AppendCheckItem(wx.ID_ANY, '&Offline Search', 'Search the local database rather than google')
  frame.offline_search.Check(system_config['offline_search'])
  self.AppendSeparator()
  frame.Bind(wx.EVT_MENU, lambda event: application.frame.Close(True), self.Append(wx.ID_EXIT, '&Quit', 'Exit the program.'))
 
 def station_from_result(self, event):
  """Create a station based on the currently focused result."""
  res = self.frame.get_result()
  if res is None:
   wx.Bell()
  else:
   station = create_station('track_id', res.id, name = 'Station based on %s' % res)
   if station is not None:
    self.frame.load_station(station)
 
 def station_from_artist(self, event):
  """Create a station based on the artist of the currently selected result."""
  res = self.frame.get_result()
  if res is None:
   wx.Bell()
  else:
   def f(artist):
    """Build the station."""
    station = create_station('artist_id', artist.id, name = 'Artist station for %s' % artist.name)
    if station is not None:
     self.frame.load_station(station)
   artist_action(res.artists, lambda artist: wx.CallAfter(f, artist))
 
 def station_from_album(self, event):
  """Build a station from an album."""
  res = self.frame.get_result()
  if res is None:
   wx.Bell()
  else:
   station = create_station('album_id', res.album_id, name = 'Album station for {artist} - {name} ({year})'.format(artist = res.artist, name = res.album, year = res.year))
   if station is not None:
    self.frame.load_station(station)
