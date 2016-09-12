"""File menu."""

import application, wx
from time import ctime
from .base import BaseMenu
from config import config
from ..create_playlist import CreatePlaylist
from ..genre_station import GenreStation
from functions.google import create_station, artist_action

class FileMenu(BaseMenu):
 """The file menu."""
 def __init__(self, parent):
  self.name = '&File'
  super(FileMenu, self).__init__()
  parent.Bind(wx.EVT_MENU, lambda event: CreatePlaylist().Show(True), self.Append(wx.ID_NEW, '&New Playlist...\tCTRL+N', 'Create a new playlist.'))
  parent.Bind(wx.EVT_MENU, lambda event: CreatePlaylist(name = 'Search Results From %s' % ctime(), tracks = application.frame.results).Show(True) if application.frame.results else wx.Bell(), self.Append(wx.ID_ANY, 'New &Playlist From Results...\tCTRL+SHIFT+N', 'Create a playlist from the currently showing results.'))
  self.AppendSeparator()
  stations_menu = wx.Menu()
  parent.Bind(wx.EVT_MENU, self.station_from_result, stations_menu.Append(wx.ID_ANY, 'From &Result...\tCTRL+9', 'Create a radio station based on the currently focused result.'))
  parent.Bind(wx.EVT_MENU, self.station_from_artist, stations_menu.Append(wx.ID_ANY, 'From &Artist...\tCTRL+SHIFT+4', 'Create a radio station based on the artist of the currently selected result.'))
  parent.Bind(wx.EVT_MENU, self.station_from_album, stations_menu.Append(wx.ID_ANY, 'From A&lbum...\tCTRL+SHIFT+5', 'Create a radio station from the album of the currently focused result.'))
  parent.Bind(wx.EVT_MENU, lambda event: GenreStation().Show(True), stations_menu.Append(wx.ID_ANY, 'From &Genre...\tCTRL+SHIFT+9', 'Create a radio station from a genre.'))
  self.AppendSubMenu(stations_menu, 'Create &Station...', 'Create a radio station from a number of sources.')
  self.AppendSeparator()
  application.frame.offline_search = self.AppendCheckItem(wx.ID_ANY, '&Offline Search', 'Search the local database rather than google')
  application.frame.offline_search.Check(config.system['offline_search'])
  application.frame.Bind(wx.EVT_MENU, lambda event: config.system.offline_search.set(bool(event.GetSelection())), application.frame.offline_search)
  self.AppendSeparator()
  parent.Bind(wx.EVT_MENU, lambda event: application.frame.Close(True), self.Append(wx.ID_EXIT))
 
 def station_from_result(self, event):
  """Create a station based on the currently focused result."""
  res = application.frame.get_result()
  if res is None:
   wx.Bell()
  else:
   station = create_station('track_id', res.id, name = 'Station based on %s' % res)
   if station is not None:
    application.frame.load_station(station)
 
 def station_from_artist(self, event):
  """Create a station based on the artist of the currently selected result."""
  res = application.frame.get_result()
  if res is None:
   wx.Bell()
  else:
   def f(artist):
    """Build the station."""
    station = create_station('artist_id', artist.id, name = 'Artist station for %s' % artist.name)
    if station is not None:
     application.frame.load_station(station)
   artist_action(res.artists, lambda artist: wx.CallAfter(f, artist))
 
 def station_from_album(self, event):
  """Build a station from an album."""
  res = application.frame.get_result()
  if res is None:
   wx.Bell()
  else:
   station = create_station('album_id', res.album_id, name = 'Album station for {artist} - {name} ({year})'.format(artist = res.artist, name = res.album, year = res.year))
   if station is not None:
    application.frame.load_station(station)
