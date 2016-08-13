"""Various widgets used throughout the program."""

import wx
from wx.lib.agw.floatspin import FloatSpin as _FloatSpin

class FloatSpin(_FloatSpin):
 """A FloatSpin which only allows 2 digits."""
 def __init__(self, *args, **kwargs):
  kwargs['digits'] = 2
  super(FloatSpin, self).__init__(*args, **kwargs)

class StringChoice(wx.Choice):
 """A wx.Coice which returns strings from GetValue and takes a string for SetValue."""
 def __init__(self, panel, value, choices):
  super(StringChoice, self).__init__(panel, choices = choices)
  self.SetValue(value)
 
 def GetValue(self):
  """Get the value of this control as a string."""
  return self.GetStringSelection()
 
 def SetValue(self, value):
  """Set the value of this control."""
  return self.SetStringSelection(value)

