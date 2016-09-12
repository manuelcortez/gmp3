"""Playlists menu."""

import wx, application
from functions.google import playlist_action
from db import Playlist, session

class PlaylistsMenu(wx.Menu):
 """A menu to show all the playlists."""
 def __init__(self, parent, add_playlists = True):
  self.parent = parent
  super(PlaylistsMenu, self).__init__()
  parent.Bind(wx.EVT_MENU, lambda event: playlist_action('Select a playlist to load', 'Playlists', lambda playlist: application.frame.add_results(playlist.tracks, showing = playlist)) if application.frame.playlist_action is None else wx.Bell(), self.Append(wx.ID_ANY, '&Remote...%s' % ('\tCTRL+1' if parent is application.frame else ''), 'Load a playlist from google.'))
  parent.Bind(wx.EVT_MENU, application.frame.edit_playlist, self.Append(wx.ID_ANY, '&Edit Playlist...%s' % ('\tCTRL+SHIFT+E' if parent is application.frame else ''), 'Edit or delete a playlist.'))
  if add_playlists:
   for p in session.query(Playlist).order_by(Playlist.name.desc()).all():
    self.add_playlist(p)
 
 def add_playlist(self, playlist, id = wx.ID_ANY):
  """Add a playlist to this menu."""
  self.parent.Bind(wx.EVT_MENU, lambda event, playlist = playlist: application.frame.add_results(playlist.tracks, showing = playlist), self.Insert(0, id, '&%s' % playlist.name, playlist.description))
