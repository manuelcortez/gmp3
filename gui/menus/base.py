"""Base menu."""

import wx, application

class BaseMenu(wx.Menu):
 name = '&Untitled'

def get_id(callback):
 """Get a new ID and bind callback to it."""
 id = wx.NewId()
 application.frame.Bind(wx.EVT_MENU, callback, id = id)
 return id
