"""Utility functions."""

import application, wx, os, os.path, logging
from db import session, Track, Playlist, Station, PlaylistEntry, to_object
from gui.login_frame import LoginFrame
from config import config
from gmusicapi.exceptions import AlreadyLoggedIn
from sqlalchemy.orm.exc import NoResultFound
from gmusicapi.exceptions import NotLoggedIn

logger = logging.getLogger(__name__)

def do_login(callback = lambda *args, **kwargs: None, args = [], kwargs = {}):
 """Try to log in, then call callback."""
 def f(callback, *args, **kwargs):
  application.logging_in = False # Free it up so more login attempts can be made if needed.
  return callback(*args, **kwargs)
 if application.logging_in:
  return # Don't try again.
 application.logging_in = True
 args.insert(0, callback)
 try:
  if not application.api.login(config.login['uid'], config.login['pwd'], application.api.FROM_MAC_ADDRESS):
   return LoginFrame(callback = f, args = args, kwargs = kwargs).Show(True)
 except AlreadyLoggedIn:
  pass
 return f(*args, **kwargs)

def load_playlist(playlist):
 """Load a playlist into the database."""
 try:
  p = session.query(Playlist).filter(Playlist.id == playlist['id']).one()
 except NoResultFound:
  p = Playlist()
  p.id = playlist['id']
 session.add(p)
 p.name = playlist.get('name', 'Untitled Playlist')
 p.description = playlist.get('description', '')
 p.tracks = []
 for t in playlist.get('tracks', []):
  if 'track' in t:
   track = to_object(t['track'])
   p.tracks.append(track)
   i = t['id']
   try:
    e = session.query(PlaylistEntry).filter(PlaylistEntry.id == i, PlaylistEntry.track == track, PlaylistEntry.playlist == p).one()
   except NoResultFound:
    e = PlaylistEntry(playlist = p, track = track, id = t['id'])
   session.add(e)
 session.commit()
 application.frame.add_playlist(p)
 return p

def do_error(message, title = 'Error'):
 return wx.MessageBox(message, title, style = wx.ICON_EXCLAMATION)

def delete_playlist(playlist):
 """Delete a playlist."""
 try:
  if application.api.delete_playlist(playlist.id) == playlist.id:
   for e in playlist.entries:
    session.delete(e)
   session.delete(playlist)
   if playlist in application.frame.playlists:
    application.frame.playlists_menu.Delete(application.frame.playlists[playlist])
    del application.frame.playlists[playlist]
   session.commit()
   return True
  else:
   return False
 except NotLoggedIn:
  do_login(callback = delete_playlist, args = [playlist])
  return True

def format_track(track):
 """Return track printed as the user likes."""
 return config.interface['track_format'].format(**{x: getattr(track, x) for x in dir(track) if not x.startswith('_')})

def load_station(station):
 """Return a Station object from a dictionary."""
 try:
  s = session.query(Station).filter(Station.id == station['id']).one()
 except NoResultFound:
  s = Station()
  s.id = station['id']
 session.add(s)
 s.name = station.get('name', 'Untitled Radio Station')
 application.frame.add_station(s)
 return s

def clean_library():
 """Remove unwanted files and directories from the media directory."""
 dir = config.storage['media_dir']
 for thing in os.listdir(dir):
  path = os.path.join(dir, thing)
  if os.path.isdir(path):
   os.removedirs(path)
  else:
   id, ext = os.path.splitext(thing)
   if not session.query(Track).filter(Track.id == id).count():
    os.remove(path)

def prune_library():
 """Delete the least recently downloaded tracks in the catalogue."""
 goal = application.library_size - config.storage['max_size'] * (1024 ** 2)
 if goal > 0:
  logger.info('Pruning %.2f mb of data...', goal / (1024 ** 2))
  for r in session.query(Track).filter(Track.last_played != None).order_by(Track.last_played.asc()).all():
   if r.downloaded:
    size = os.path.getsize(r.path)
    logger.info('Deleting %s (%.2f mb).', r, size / (1024 ** 2))
    goal -= size
    application.library_size -= size
    os.remove(r.path)
    if goal <= 0:
     logger.info('Done.')
     break
  else:
   logger.info('Failed. %s b (%.2f mb) left.', goal, goal / (1024 ** 2))
 else:
  logger.info('No need for prune. %.2f mb left.', (goal * -1) / (1024 ** 2))
