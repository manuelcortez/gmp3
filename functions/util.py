"""Utility functions."""

import application, wx
from db import session, Playlist, Station, PlaylistEntry, to_object
from config import interface_config
from gui.login_frame import LoginFrame
from gmusicapi.exceptions import AlreadyLoggedIn
from sqlalchemy.orm.exc import NoResultFound
from config import login_config
from gmusicapi.exceptions import NotLoggedIn

def do_login(callback = lambda *args, **kwargs: None, args = [], kwargs = {}):
 """Try to log in, then call callback."""
 try:
  if not application.api.login(login_config['uid'], login_config['pwd'], application.api.FROM_MAC_ADDRESS):
   return LoginFrame(callback = callback, args = args, kwargs = kwargs).Show(True)
 except AlreadyLoggedIn:
  pass
 return callback(*args, **kwargs)

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
 return interface_config['track_format'].format(**{x: getattr(track, x) for x in dir(track) if not x.startswith('_')})

def load_station(station):
 """Return a Station object from a dictionary."""
 try:
  s = session.query(Station).filter(Station.id == station['id']).one()
 except NoResultFound:
  s = Station()
 session.add(s)
 s.id = station['id']
 s.name = station.get('name', 'Untitled Radio Station')
 application.frame.add_station(s)
 return s
