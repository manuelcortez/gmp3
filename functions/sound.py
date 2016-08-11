"""Sound-related functions."""

import application, logging
from threading import Thread
from datetime import datetime
from .util import do_login
from .network import download_track
from config import storage_config, system_config
from showing import SHOWING_QUEUE
from sound_lib.stream import FileStream, URLStream
from gmusicapi.exceptions import NotLoggedIn
logger = logging.getLogger(__name__)

seek_amount = 100000

def play(track, play = True):
 """Play a track."""
 if track is None:
  return # There's no track left to play.
 if track is application.track and application.stream:
  track = application.track
  stream = application.stream
 elif not track.downloaded:
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
 track.last_played = datetime.now()
 if application.stream is not None:
  application.stream.stop()
 if play:
  stream.play(True)
 application.stream = stream
 set_pan(system_config['pan'])
 set_frequency(system_config['frequency'])
 application.frame.SetTitle()
 application.frame.update_labels()
 return stream

def get_next(remove = True):
 """Get the next track which should be played. If remove == True, delete the track from the queue if that's where it came from."""
 if application.frame.repeat_track.IsChecked():
  return application.track
 t = None
 if application.frame.queue:
  t = application.frame.queue[0]
  if remove:
   application.frame.queue.remove(t)
 else:
  try:
   t = application.frame.results[application.frame.results.index(application.track) + 1]
  except IndexError: # We're at the end.
   if application.frame.results and application.frame.repeat_all.IsChecked():
    t = application.frame.results[0]
   else:
    pass # t is already None.
  except ValueError: # The view has changed.
   try:
    t = application.frame.results[0]
   except IndexError:
    pass # t is already None.
 return t

def get_previous():
 """Get the previous track."""
 if application.frame.repeat_track.IsChecked():
  return application.track
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
 if application.frame.showing == SHOWING_QUEUE:
  application.frame.add_results([track], clear = False)

def unqueue(track):
 """Remove track from the queue."""
 application.frame.queue.remove(track)
 application.frame.update_labels()
 if application.frame.showing == SHOWING_QUEUE:
  application.frame.remove_result(track)

def seek(amount):
 """Seek through the current track."""
 application.stream.set_position(max(0, min(application.stream.get_length(), application.stream.get_position() + amount)))

def set_output_device(name):
 """Given a device name, change the output device."""
 device = application.output.find_device_by_name(name)
 if device != application.output.device:
  try:
   to_play = application.stream.is_playing
   pos = application.stream.get_position()
  except AttributeError: # There is no stream playing
   to_play = True
   pos = 0
  application.output.set_device(device)
  logger.info('Set output device to %s (%s).', name, device)
  application.stream = None # Calling .stop() on a stream after it's device has been dropped causes a traceback.
  s = play(application.track, play = to_play)
  if s is not None:
   s.set_position(pos)
  system_config['output_device_index'] = device
  system_config['output_device_name'] = name
