"""The main menu bar."""

import wx, logging
from .file import FileMenu
from .play import PlayMenu
from .source import SourceMenu
from .track import TrackMenu
from .options import OptionsMenu

logger = logging.getLogger(__name__)

class MainMenu(wx.MenuBar):
 """The main menu bar."""
 def __init__(self, frame):
  super(MainMenu, self).__init__()
  for Menu in [
   FileMenu,
   PlayMenu,
   SourceMenu,
   TrackMenu,
   OptionsMenu,
  ]:
   m = Menu(frame)
   logger.info('Created menu %s (%s).', m.name, m)
   self.Append(m, m.name)
