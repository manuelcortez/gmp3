"""Options menu."""

import wx
from configobj_dialog import ConfigObjDialog
from ..audio_options import AudioOptions
from .base import BaseMenu
from config import sections

class OptionsMenu(BaseMenu):
 """The options menu."""
 def __init__(self, frame):
  self.name = '&Options'
  super(OptionsMenu, self).__init__()
  for section in sections:
   frame.Bind(wx.EVT_MENU, lambda event, section = section: ConfigObjDialog(section).Show(True), self.Append(wx.ID_ANY, '&%s...' % section.title, 'Edit the %s configuration.' % section.title))
  frame.Bind(wx.EVT_MENU, lambda event: AudioOptions(), self.Append(wx.ID_ANY, '&Audio...\tF12', 'Configure advanced audio settings.'))
