"""Internet-related functions."""

import os, os.path
from requests import get

def download_track(url, path):
 """Download URL to path."""
 response = get(url)
 folder = os.path.dirname(path)
 if not os.path.isdir(folder):
  os.makedirs(folder)
 with open(path, 'wb') as f:
  f.write(response.content)

