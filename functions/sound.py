"""Sound-related functions."""

import application, logging
from threading import Thread
from math import pow
from datetime import datetime
from random import choice
from time import time, sleep
from .util import do_login, do_error
from .network import download_track
from showing import SHOWING_QUEUE
from config import config
from sound_lib.stream import FileStream, URLStream
from gmusicapi.exceptions import NotLoggedIn

logger = logging.getLogger(__name__)

seek_amount = 100000

try:
 from pyglet.media import load, Player
 player = Player()
except ImportError:
 player = None # No pyglet on this system.

class PygletFileStream(object):
 """A stream that will play pyglet MP3's."""
 @property
 def volume(self):
  return self.get_volume()
 
 @volume.setter
 def volume(self, value):
  self.set_volume(value)
 
 def __init__(self, filename):
  player.queue(load(filename))
  self.is_paused = False
  self.is_stopped = False
 
 def play(self, restart = False):
  if not hasattr(player, 'has_played'):
   player.next()
   player.has_played = True # Don't do that again.
  if restart:
   self.set_position(0.0)
  player.play()
 
 def get_position(self):
  return player.time
 
 def set_position(self, value):
  try:
   player.seek(value)
  except AttributeError:
   pass # No source to seek.
 
 def get_length(self):
  try:
   return player.source.duration
  except AttributeError:
   return 0.0 # No source.
 
 def pause(self):
  player.pause()
  self.is_paused = True
 
 def stop(self):
  player.pause()
  self.set_position(0.0)
  self.is_stopped = True
 
 def get_volume(self):
  return player.volume
 
 def set_volume(self, value):
  player.volume = value
 
 def get_frequency(self):
  return 44100.0
 
 def set_frequency(self, value):
  pass
 
 def get_pan(self):
  return 0.0
 
 def set_pan(self, value):
  pass

def play(track, immediately_play = True):
 """Play a track."""
 if track is not None:
  if track is application.track and application.stream:
   stream = application.stream
  elif not track.downloaded:
   try:
    url = application.api.get_stream_url(track.id)
    if track.artists[0].bio is None:
     track.artists[0].populate(application.api.get_artist_info(track.artists[0].id))
    if not config.sound['pyglet']:
     stream = URLStream(url.encode())
    if config.storage['download'] or config.sound['pyglet']:
     if config.sound['pyglet']:
      download_track(url, track.path)
      play(track, immediately_play = immediately_play)
     else:
      Thread(target = download_track, args = [url, track.path]).start()
   except NotLoggedIn:
    return do_login(callback = play, args = [track])
  else:
   if config.sound['pyglet']:
    try:
     stream = PygletFileStream(track.path)
    except Exception as e:
     return do_error('Error playing track %s: %s' % (track, e))
   else:
    stream = FileStream(file = track.path)
  track.last_played = datetime.now()
  if stream is not application.stream and application.stream is not None:
   if config.sound['pyglet']:
    application.stream.pause()
   else:
    Thread(target = fadeout, args = [application.stream]).start()
  if immediately_play:
   stream.play(True)
   if config.interface['notify']:
    application.frame.tb_icon.notify('Now playing %s.' % track)
  set_volume(config.system['volume'])
  set_pan(config.system['pan'])
  set_frequency(config.system['frequency'])
 else:
  track = None
  stream = None
 if application.track is not track:
  Thread(target = application.frame.update_lyrics, args = [track]).start()
 application.track = track
 application.stream = stream
 application.frame.SetTitle()
 application.frame.update_labels()
 return stream

def get_next(remove = True):
 """Get the next track which should be played. If remove == True, delete the track from the queue if that's where it came from."""
 if hasattr(application.frame, 'repeat_track') and application.frame.repeat_track.IsChecked():
  return application.track
 t = None
 if application.frame is not None and application.frame.queue:
  t = application.frame.queue[0]
  if remove:
   application.frame.queue.remove(t)
 else:
  if hasattr(application.frame, 'shuffle') and application.frame.shuffle.IsChecked():
   if remove:
    if len(application.frame.played) == len(application.frame.results):
     application.frame.played.clear()
    t = choice([x for x in application.frame.results if x not in application.frame.played])
    application.frame.played.append(t)
    return t
   else:
    return None
  try:
   t = application.frame.results[application.frame.results.index(application.track) + 1]
  except (IndexError, AttributeError): # We're at the end.
   if application.frame is not None and application.frame.results and hasattr(application.frame, 'repeat_all') and application.frame.repeat_all.IsChecked():
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
 if hasattr(application.frame, 'repeat_track') and application.frame.repeat_track.IsChecked():
  return application.track
 try:
  return application.frame.results[application.frame.results.index(application.track) - 1]
 except (IndexError, ValueError, AttributeError):
  return None

def set_volume(value):
 """Set volume to value."""
 actual_value = ((pow(config.sound['volume_base'], value / 100) - 1) / (config.sound['volume_base'] - 1)) * 100
 config.system['volume'] = value
 if config.sound['pyglet']:
  if application.stream:
   application.stream.set_volume(actual_value / 100.0)
 else:
  application.output.set_volume(actual_value)
 application.frame.volume.SetValue(value)
 logger.info('Set volume to %.2f (%s%%).', actual_value, value)

def set_pan(value):
 """Set pan to value."""
 config.system['pan'] = value
 if application.stream:
  application.stream.set_pan(value * 2 / 100 - 1.0)

def set_frequency(value):
 """Set frequency to value."""
 config.system['frequency'] = value
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
  s = play(application.track, immediately_play = to_play)
  if s is not None:
   s.set_position(pos)
  config.system['output_device_index'] = device
  config.system['output_device_name'] = name

def fadeout(stream):
 """Fade out and stop a stream."""
 started = time()
 logger.info('Fading out stream %s.', stream)
 while stream.volume > 0.0:
  v = max(0.0, stream.volume - config.sound['fadeout_amount'])
  logger.info('Setting stream volume to %.2f.', v)
  stream.volume = v
  sleep(0.2)
 stream.stop()
 logger.info('Stopped the stream after %.2f seconds.', time() - started)

