"""Sound-related functions."""

import application
from threading import Thread
from .util import do_login
from .network import download_track
from config import storage_config
from sound_lib.stream import FileStream, URLStream
from gmusicapi.exceptions import NotLoggedIn

def play(track):
 """Play a track."""
 if not track.downloaded:
  try:
   url = application.api.get_stream_url(track.id)
   stream = URLStream(url.encode())
   if storage_config['download']:
    Thread(target = download_track, args = [url, track.path]).start()
  except NotLoggedIn:
   return do_login(callback = play, args = [track])
 else:
  stream = FileStream(file = track.path)
 if application.track is not None:
  application.track.stop()
 application.track = stream
 stream.play()
