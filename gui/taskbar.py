"""This file contains the task bar icon class."""

import wx, application
from wx.adv import TaskBarIcon as _TaskBarIcon
from .menus.taskbar import TaskBarMenu

class TaskBarIcon(_TaskBarIcon):
 def __init__(self):
  super(TaskBarIcon, self).__init__()
  self.SetIcon(wx.Icon(wx.Bitmap('icon.png')), '%s V%s' % (application.name, application.__version__))
 
 def CreatePopupMenu(self):
  """Get the right click menu."""
  return TaskBarMenu(self)
 
 def notify(self, message):
  """Notify the user of something."""
  return self.ShowBalloon(application.name, message)
