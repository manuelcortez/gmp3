"""File menu."""

import application, wx
from .base import BaseMenu
from config import system_config

class FileMenu(BaseMenu):
 """The file menu."""
 def __init__(self, frame):
  self.name = '&File'
  super(FileMenu, self).__init__()
  frame.offline_search = self.AppendCheckItem(wx.ID_ANY, '&Offline Search', 'Search the local database rather than google')
  frame.offline_search.Check(system_config['offline_search'])
  self.AppendSeparator()
  frame.Bind(wx.EVT_MENU, lambda event: application.frame.Close(True), self.Append(wx.ID_EXIT, '&Quit', 'Exit the program.'))
