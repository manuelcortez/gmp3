"""Internet-related functions."""

import application, wx, os, os.path
from requests import get
from .util import prune_library

def download_track(url, path):
 """Download URL to path."""
 response = get(url)
 folder = os.path.dirname(path)
 if not os.path.isdir(folder):
  os.makedirs(folder)
 with open(path, 'wb') as f:
  application.library_size += f.write(response.content)
 wx.CallAfter(prune_library) # Delete old tracks if necessry.
