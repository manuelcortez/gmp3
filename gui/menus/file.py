"""File menu."""

import application, wx
from time import ctime
from .base import BaseMenu
from config import system_config
from ..create_playlist import CreatePlaylist

class FileMenu(BaseMenu):
 """The file menu."""
 def __init__(self, frame):
  self.name = '&File'
  super(FileMenu, self).__init__()
  frame.Bind(wx.EVT_MENU, lambda event: CreatePlaylist().Show(True), self.Append(wx.ID_ANY, '&New Playlist...\tCTRL+N', 'Create a new playlist.'))
  frame.Bind(wx.EVT_MENU, lambda event: CreatePlaylist(name = 'Search Results From %s' % ctime(), tracks = frame.results).Show(True) if frame.results else wx.Bell(), self.Append(wx.ID_ANY, 'New &Playlist From Results...\tCTRL+SHIFT+N', 'Create a playlist from the currently showing results.'))
  frame.offline_search = self.AppendCheckItem(wx.ID_ANY, '&Offline Search', 'Search the local database rather than google')
  frame.offline_search.Check(system_config['offline_search'])
  self.AppendSeparator()
  frame.Bind(wx.EVT_MENU, lambda event: application.frame.Close(True), self.Append(wx.ID_EXIT, '&Quit', 'Exit the program.'))
