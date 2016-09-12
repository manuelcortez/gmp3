"""Taskbar menu."""

import wx, application, logging
from .play import PlayMenu
from .source import SourceMenu

logger = logging.getLogger(__name__)

class TaskBarMenu(wx.Menu):
 """The menu that is shown when the taskbar parent is clicked."""
 def __init__(self, parent):
  logger.info('Creating menu with parent %s.', parent)
  super(TaskBarMenu, self).__init__()
  frame = application.frame
  parent.Bind(wx.EVT_MENU, lambda event: application.frame.add_command(frame.Show, not frame.Shown), self.Append(wx.ID_ANY, '&%s' % ('Hide' if application.frame.Shown else 'Show')))
  self.Append(wx.ID_ANY, 'Nothing playing' if application.track is None else ('Now playing: %s' % application.track)).Enable(False)
  for menu in [
   PlayMenu,
   SourceMenu
  ]:
   logger.info('Creating menu from base class %s.', menu)
   m = menu(parent)
   logger.info('Created %s.', m)
   self.AppendSubMenu(m, m.name)
  parent.Bind(wx.EVT_MENU, lambda event: application.frame.add_command(application.frame.Close, True), self.Append(wx.ID_EXIT))
