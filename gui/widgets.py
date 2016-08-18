"""Various widgets used throughout the program."""

import wx

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

