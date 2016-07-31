"""Internet-related functions."""

import os, os.path
from requests import get
from application import api

def download_track(track):
 """Download a track to disk."""
 url = api.get_stream_url(track.id)
 response = get(url)
 folder = os.path.dirname(track.path)
 if not os.path.isdir(folder):
  os.makedirs(folder)
 with open(track.path, 'wb') as f:
  f.write(response.content)

