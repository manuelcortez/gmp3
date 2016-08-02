"""Sound-related functions."""

import application
from threading import Thread
from .util import do_login
from .network import download_track
from config import storage_config
from sound_lib.stream import FileStream, URLStream
from gmusicapi.exceptions import NotLoggedIn

def play_threaded(stream):
 """Play a stream in a blocking manner before going on to play the next track."""
 stream.play_blocking()
 if application.stream is stream:
  t = get_next(remove = True)
  if t:
   play(t)

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
 application.track = track
 Thread(target = play_threaded, args = [stream]).start()
 old_stream = application.stream
 application.stream = stream
 if old_stream is not None:
  old_stream.stop()
 application.frame.update_labels()

def get_next(remove = True):
 """Get the next track which should be played. If remove == True, delete the track from the queue if that's where it came from."""
 if application.frame.queue:
  t = application.frame.queue[0]
  if remove:
   application.frame.queue.remove(t)
 else:
  try:
   t = application.frame.results[application.frame.results.index(application.track) + 1]
  except IndexError:
   return None
  except ValueError:
   try:
    t = application.frame.results[0]
   except IndexError:
    return None
 return t

def get_previous():
 """Get the previous track."""
 try:
  return application.frame.results[application.frame.results.index(application.track) - 1]
 except (IndexError, ValueError):
  return None
