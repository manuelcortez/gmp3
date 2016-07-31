"""Sound-related functions."""

import application
from .util import do_login
from .network import download_track
from sound_lib.stream import FileStream
from gmusicapi.exceptions import NotLoggedIn

def play(track):
 """Play a track."""
 if not track.downloaded:
  try:
   download_track(track)
  except NotLoggedIn:
   return do_login(callback = play, args = [track])
 s = FileStream(file = track.path)
 if application.track is not None:
  application.track.stop()
 application.track = s
 s.play()
