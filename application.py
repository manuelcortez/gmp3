"""Application specific storage."""

import wx
from sound_lib.output import Output
from gmusicapi import Mobileclient

name = 'GMP3'
__version__ = '4.3.0'
db_version = 1
url = 'https://github.com/chrisnorman7/gmp3'


app = wx.App(False)
app.SetAppName(name)
paths = wx.StandardPaths.Get()

output = Output()

api = Mobileclient()
api.android_id = '123456789abcde'

frame = None  # The main window.
track = None  # The current track.
stream = None  # The stream of the currently playing track.

library_size = 0  # The size of the library in bytes.
# Prevent the killer bug that makes the timer try and pop up billions of login
# windows:
logging_in = False
