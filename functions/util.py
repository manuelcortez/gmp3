"""Utility functions."""

from gui.login_frame import LoginFrame
from gmusicapi.exceptions import AlreadyLoggedIn
from application import api
from config import login_config

def do_login(callback = lambda *args, **kwargs: None, args = [], kwargs = {}):
 """Try to log in, then call callback."""
 try:
  if not api.login(login_config['uid'], login_config['pwd'], api.FROM_MAC_ADDRESS):
   return LoginFrame(callback = callback, args = args, kwargs = kwargs).Show(True)
 except AlreadyLoggedIn:
  pass
 return callback(*args, **kwargs)
