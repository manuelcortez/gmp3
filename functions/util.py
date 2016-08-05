"""Utility functions."""

import application, wx
from db import session, Playlist, list_to_objects
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
 p.name = playlist['name']
 p.description = playlist['description']
 p.tracks = []
 for t in list_to_objects([x['track'] for x in playlist.get('tracks', []) if 'track' in x]):
  p.tracks.append(t)
 session.commit()
 return p

def do_error(message, title = 'Error'):
 return wx.MessageBox(message, title, style = wx.ICON_EXCLAMATION)

def delete_playlist(playlist):
 """Delete a playlist."""
 try:
  if application.api.delete_playlist(playlist.id) == playlist.id:
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
