"""Application specific storage."""

import wx

name = 'GMP3'
__version__ = '3.1'

app = wx.App(False)
app.SetAppName(name)
paths = wx.StandardPaths.Get()

from sound_lib.output import Output
output = Output()

from gmusicapi.clients import Mobileclient
api = Mobileclient()
api.android_id = '123456789abcde'

frame = None # The main window.
track = None # The current track.
stream = None # The stream of the currently playing track.

library_size = 0 # The size of the library in bytes.
logging_in = False # To prevent the killer bug that makes the timer try and pop up billions of login windows.
