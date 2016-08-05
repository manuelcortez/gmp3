"""Sound-related functions."""

import application
from threading import Thread
from .util import do_login
from .network import download_track
from config import storage_config, system_config
from sound_lib.stream import FileStream, URLStream
from gmusicapi.exceptions import NotLoggedIn

seek_amount = 100000

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
 if application.stream is not None:
  application.stream.stop()
 stream.play(True)
 application.stream = stream
 set_pan(system_config['pan'])
 set_frequency(system_config['frequency'])
 application.frame.SetTitle(str(track))
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

def set_volume(value):
 """Set volume to value."""
 system_config['volume'] = value
 application.output.set_volume(value)
 application.frame.volume.SetValue(value)

def set_pan(value):
 """Set pan to value."""
 system_config['pan'] = value
 if application.stream:
  application.stream.set_pan(value * 2 / 100 - 1.0)

def set_frequency(value):
 """Set frequency to value."""
 system_config['frequency'] = value
 if application.stream:
  application.stream.set_frequency(value)

def queue(track):
 """Add track to the play queue."""
 application.frame.queue.append(track)
 application.frame.update_labels()

def unqueue(track):
 """Remove track from the queue."""
 application.frame.queue.remove(track)
 application.frame.update_labels()

def seek(amount):
 """Seek through the current track."""
 application.stream.set_position(max(0, min(application.stream.get_length(), application.stream.get_position() + amount)))
