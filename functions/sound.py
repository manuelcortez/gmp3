"""Sound-related functions."""

import application, wx
from threading import Thread
from .util import do_login
from .network import download_track
from config import storage_config
from sound_lib.stream import FileStream, URLStream
from gmusicapi.exceptions import NotLoggedIn

def play_threaded(stream):
 """Play a stream in a blocking manner before going on to play the next track."""
 application.stream = stream
 wx.CallAfter(application.frame.SetTitle, str(application.track))
 wx.CallAfter(application.frame.update_labels)
 stream.play_blocking(True)
 if stream is application.stream:
  t = get_next(remove = True)
  if t:
   play(t, thread = False)

def play(track, thread = True):
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
 if application.stream is not None:
  old_stream = application.stream
  application.stream = None
  old_stream.stop()
 if thread: # Play the stream in another thread.
  Thread(target = play_threaded, args = [stream]).start()
 else:
  play_threaded(stream)

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
