"""Play menu."""

import wx, application, logging
from .base import BaseMenu
from functions.sound import queue, set_volume, get_previous, get_next
from config import config

logger = logging.getLogger(__name__)

class PlayMenu(BaseMenu):
 """The play menu."""
 def __init__(self, parent):
  self.name = '&Play'
  super(PlayMenu, self).__init__()
  parent.Bind(wx.EVT_MENU, application.frame.play_pause, self.Append(wx.ID_ANY, '&Play / Pause', 'Play or pause the current track.'))
  parent.Bind(wx.EVT_MENU, application.frame.do_stop, self.Append(wx.ID_ANY, '&Stop\tCTRL+.', 'Stop the currently playing track.'))
  stop_after = self.AppendCheckItem(wx.ID_ANY, 'Stop &After Current Track\tCTRL+SHIFT+.', 'Stop when the currently playing track has finished playing.')
  stop_after.Check(config.system['stop_after'])
  parent.Bind(wx.EVT_MENU, lambda event: application.frame.add_command(self.do_stop_after, bool(event.GetSelection())), stop_after)
  if not hasattr(application.frame, 'stop_after'):
   application.frame.stop_after = stop_after
  parent.Bind(wx.EVT_MENU, lambda event: queue(application.frame.get_result()) if application.frame.get_result() is not None else wx.Bell(), self.Append(wx.ID_ANY, '&Queue Item\tSHIFT+RETURN', 'Add the currently focused track to the play queue.'))
  parent.Bind(wx.EVT_MENU, application.frame.on_previous, self.Append(wx.ID_ANY, '&Previous Track%s\tCTRL+LEFT' % ('' if get_previous() is None else ' (%s)' % (get_previous())), 'Play the previous track.'))
  parent.Bind(wx.EVT_MENU, application.frame.on_next, self.Append(wx.ID_ANY, '&Next Track%s\tCTRL+RIGHT' % ('' if get_next(False) is None else ' (%s)' % (get_next(remove = False))), 'Play the next track.'))
  parent.Bind(wx.EVT_MENU, lambda event: set_volume(max(0, application.frame.volume.GetValue() - 5)), self.Append(wx.ID_ANY, 'Volume &Down\tCTRL+DOWN', 'Reduce volume by 5%.'))
  parent.Bind(wx.EVT_MENU, lambda event: set_volume(min(100, application.frame.volume.GetValue() + 5)), self.Append(wx.ID_ANY, 'Volume &Up\tCTRL+UP', 'Increase volume by 5%.'))
  repeat_menu = wx.Menu()
  self.repeat_off = repeat_menu.AppendRadioItem(wx.ID_ANY, '&Off', 'No repeat.')
  self.repeat_track = repeat_menu.AppendRadioItem(wx.ID_ANY, '&Track', 'Repeat just the currently playing track.')
  self.repeat_all = repeat_menu.AppendRadioItem(wx.ID_ANY, '&All', 'Repeat all.')
  wx.CallAfter([self.repeat_off, self.repeat_track, self.repeat_all][config.system['repeat']].Check, True)
  for value, option in enumerate(['repeat_off', 'repeat_track', 'repeat_all']):
   control = getattr(self, option)
   parent.Bind(wx.EVT_MENU, lambda event, value = value: config.system.repeat.set(value), control)
   if not hasattr(application.frame, option):
    setattr(application.frame, option, control)
  self.AppendSubMenu(repeat_menu, '&Repeat')#, 'Repeat options')
  shuffle = self.AppendCheckItem(wx.ID_ANY, '&Shuffle\tCTRL+H', 'Play all tracks shuffled.')
  parent.Bind(wx.EVT_MENU, lambda event: application.frame.add_command(self.do_shuffle, bool(event.GetSelection())), shuffle)
  shuffle.Check(config.system['shuffle'])
  if not hasattr(application.frame, 'shuffle'):
   application.frame.shuffle = shuffle
  parent.Bind(wx.EVT_MENU, parent.cast_result, self.Append(wx.ID_ANY, '&Cast...\tF11', 'Cast the currently-focused item'))
 
 def do_stop_after(self, value):
  """Setup stop_after."""
  config.system['stop_after'] = value
  application.frame.stop_after.Check(value)
  application.frame.tb_icon.notify('%s after the current track.' % ('Stop ' if value else 'Don\'t stop'))
 
 def do_shuffle(self, value):
  """Organise the shuffle."""
  if value:
   application.frame.playing = []
  config.system['shuffle'] = value
  application.frame.tb_icon.notify('Shuffle %s.' % ('on' if value else 'off'))
