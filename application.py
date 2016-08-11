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

frame = None # The main window.
track = None # The current track.
locked = False # Set to True when the track is locked.
stream = None # The stream of the currently playing track.
old_stream = None # The stream which is just finishing.
