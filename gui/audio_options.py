"""Audio options window."""

from wx.lib.sized_controls import SizedFrame
from wx.lib.intctrl import IntCtrl, EVT_INT
from wxgoodies.keys import add_accelerator
from config import config, min_frequency, max_frequency
from functions.sound import set_output_device, set_volume, set_pan, set_frequency
import application, wx

class AudioOptions(SizedFrame):
 def __init__(self):
  super(AudioOptions, self).__init__(application.frame, title = 'Audio Options')
  p = self.GetContentsPane()
  add_accelerator(self, 'ESCAPE', lambda event: self.Close(True))
  self.default_volume = config.system['volume']
  self.default_frequency = config.system['frequency']
  self.default_pan = config.system['pan']
  p.SetSizerType('form')
  wx.StaticText(p, label = '&Output Device')
  self.device = wx.Choice(p, choices = sorted(application.output.get_device_names()))
  self.device.SetStringSelection(config.system['output_device_name'])
  self.device.Bind(wx.EVT_CHOICE, lambda event: set_output_device(self.device.GetStringSelection()))
  wx.StaticText(p, label = '&Volume')
  self.volume = wx.Slider(p, style = wx.VERTICAL)
  self.volume.SetValue(self.default_volume)
  self.volume.Bind(wx.EVT_SLIDER, lambda event: set_volume(self.volume.GetValue()))
  wx.StaticText(p, label = '&Pan')
  self.pan = wx.Slider(p, style = wx.HORIZONTAL)
  self.pan.SetValue(self.default_pan)
  self.pan.Bind(wx.EVT_SLIDER, lambda event: set_pan(self.pan.GetValue()))
  wx.StaticText(p, label = '&Frequency')
  self.frequency = IntCtrl(p, value = self.default_frequency, min = min_frequency, max = max_frequency, limited = True)
  self.frequency.Bind(EVT_INT, set_frequency(self.frequency.GetValue()))
  add_accelerator(self.frequency, 'UP', lambda event: self.update_frequency(min(self.frequency.GetMax(), self.frequency.GetValue() + 100)))
  add_accelerator(self.frequency, 'DOWN', lambda event: self.update_frequency(max(self.frequency.GetMin(), self.frequency.GetValue() - 100)))
  self.ok = wx.Button(p, label = '&OK')
  self.ok.Bind(wx.EVT_BUTTON, lambda event: self.Close(True))
  self.restore = wx.Button(p, label = '&Restore Defaults')
  self.restore.Bind(wx.EVT_BUTTON, self.on_restore)
  self.Show(True)
  self.Maximize(True)
 
 def update_frequency(self, value):
  """Update frequency."""
  self.frequency.SetValue(value)
  set_frequency(value)
 
 def on_restore(self, event):
  """Cancel button was pressed."""
  set_volume(100)
  set_pan(50)
  set_frequency(44100)
