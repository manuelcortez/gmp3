"""Application specific storage."""

import wx

name = 'GMP3'
__version__ = '3.0'

app = wx.App()
app.SetAppName(name)
paths = wx.StandardPaths.Get()

from sound_lib.output import Output
output = Output()

from gmusicapi.clients import Mobileclient
api = Mobileclient()
api.android_id = '123456789abcde'
