"""Play menu."""

import wx
from wxgoodies.keys import add_accelerator
from .base import BaseMenu
from functions.sound import queue, set_volume
from config import config

class PlayMenu(BaseMenu):
 """The play menu."""
 def __init__(self, frame):
  self.name = '&Play'
  super(PlayMenu, self).__init__()
  frame.Bind(wx.EVT_MENU, frame.play_pause, self.Append(wx.ID_ANY, '&Play / Pause', 'Play or pause the current track.'))
  frame.Bind(wx.EVT_MENU, frame.do_stop, self.Append(wx.ID_ANY, '&Stop\tCTRL+.', 'Stop the currently playlist track.'))
  frame.stop_after = self.AppendCheckItem(wx.ID_ANY, 'Stop &After Current Track\tCTRL+SHIFT+.', 'Stop when the currently playing track has finished playing.')
  frame.stop_after.Check(config.system['stop_after'])
  frame.Bind(wx.EVT_MENU, lambda event: queue(frame.get_result()) if frame.get_result() is not None else wx.Bell(), self.Append(wx.ID_ANY, '&Queue Item\tSHIFT+RETURN', 'Add the currently focused track to the play queue.'))
  frame.Bind(wx.EVT_MENU, frame.on_previous, self.Append(wx.ID_ANY, '&Previous Track\tCTRL+LEFT', 'Play the previous track.'))
  frame.Bind(wx.EVT_MENU, frame.on_next, self.Append(wx.ID_ANY, '&Next Track\tCTRL+RIGHT', 'Play the next track.'))
  frame.Bind(wx.EVT_MENU, lambda event: set_volume(max(0, frame.volume.GetValue() - 5)), self.Append(wx.ID_ANY, 'Volume &Down\tCTRL+DOWN', 'Reduce volume by 5%.'))
  frame.Bind(wx.EVT_MENU, lambda event: set_volume(min(100, frame.volume.GetValue() + 5)), self.Append(wx.ID_ANY, 'Volume &Up\tCTRL+UP', 'Increase volume by 5%.'))
  repeat_menu = wx.Menu()
  frame.repeat_off = repeat_menu.AppendRadioItem(wx.ID_ANY, '&Off', 'No repeat.')
  frame.repeat_track = repeat_menu.AppendRadioItem(wx.ID_ANY, '&Track', 'Repeat just the currently playlist track.')
  frame.repeat_all = repeat_menu.AppendRadioItem(wx.ID_ANY, '&All', 'Repeat all.')
  [frame.repeat_off, frame.repeat_track, frame.repeat_all][config.system['repeat']].Check(True)
  self.AppendSubMenu(repeat_menu, '&Repeat', 'Repeat options')
  add_accelerator(frame, 'CTRL+R', frame.cycle_repeat)
  frame.shuffle = self.AppendCheckItem(wx.ID_ANY, '&Shuffle\tCTRL+H', 'Shuffle the current view.')
  frame.shuffle.Check(config.system['shuffle'])
  self.Bind(wx.EVT_MENU, lambda event: setattr(frame, 'playing', []), frame.shuffle)
