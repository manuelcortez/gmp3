"""This file contains the task bar icon class."""

import wx, application, logging
from wx.adv import TaskBarIcon as _TaskBarIcon
from .menus.taskbar import TaskBarMenu

logger = logging.getLogger(__name__)

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
 
def Destroy(self):
  """Destroy the icon."""
  super(TaskBarIcon, self).Destroy()
  logger.info('Destroyed the taskbar icon.')

class FakeTaskBarIcon(object):
 def notify(self, message):
  """Pretend to notify."""
  logger.warning('Notification ignored by %s: %s.', self, message)
 
 def Destroy(self):
  """Pretend to destroy the taskbar icon."""
  logger.warning('No taskbar icon to destroy.')
