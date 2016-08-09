"""Source menu."""

import wx, showing
from threading import Thread
from db import session, Track
from functions.google import playlist_action
from .base import BaseMenu

class SourceMenu(BaseMenu):
 """The source menu."""
 def __init__(self, frame):
  self.name = '&Source'
  super(SourceMenu, self).__init__()
  frame.Bind(wx.EVT_MENU, lambda event: Thread(target = frame.load_library,).start(), self.Append(wx.ID_ANY, '&Library\tCTRL+L', 'Load every song in your Google Music library.'))
  frame.Bind(wx.EVT_MENU, lambda event: Thread(target = frame.load_promoted_songs).start(), self.Append(wx.ID_ANY, 'Promoted &Songs\tCTRL+P', 'Load promoted songs.'))
  frame.Bind(wx.EVT_MENU, lambda event: frame.add_results(frame.queue, showing = showing.SHOWING_QUEUE), self.Append(wx.ID_ANY, '&Queue\tCTRL+SHIFT+Q', 'Show all tracks in the play queue.'))
  frame.Bind(wx.EVT_MENU, lambda event: frame.add_results(session.query(Track).all(), showing = showing.SHOWING_CATALOGUE), self.Append(wx.ID_ANY, '&Catalogue\tCTRL+0', 'Load all songs which are stored in the local database.'))
  frame.Bind(wx.EVT_MENU, lambda event: frame.add_results([x for x in session.query(Track).all() if x.downloaded is True], showing = showing.SHOWING_DOWNLOADED), self.Append(wx.ID_ANY, '&Downloaded\tCTRL+D', 'Show all downloaded tracks.'))
  frame.playlists_menu = wx.Menu()
  frame.Bind(wx.EVT_MENU, lambda event: playlist_action('Select a playlist to load', 'Playlists', lambda playlist: frame.add_results(playlist.tracks, showing = playlist)) if frame.playlist_action is None else wx.Bell(), frame.playlists_menu.Append(wx.ID_ANY, '&Remote...\tCTRL+1', 'Load a playlist from google.'))
  frame.Bind(wx.EVT_MENU, frame.edit_playlist, frame.playlists_menu.Append(wx.ID_ANY, '&Edit Playlist...\tCTRL+SHIFT+E', 'Edit or delete a playlist.'))
  self.AppendSubMenu(frame.playlists_menu, '&Playlists', 'Select ocal or a remote playlist to view.')
  frame.stations_menu = wx.Menu()
  frame.Bind(wx.EVT_MENU, frame.load_remote_station, frame.stations_menu.Append(wx.ID_ANY, '&Remote...\tCTRL+2', 'Load a readio station from Google.'))
  frame.delete_stations_menu = wx.Menu()
  frame.stations_menu.AppendSubMenu(frame.delete_stations_menu, '&Delete')
  self.AppendSubMenu(frame.stations_menu, '&Radio Stations', 'Locally stored and remote radio stations.')
