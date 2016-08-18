"""A login frame."""

from simpleconf.dialogs.wx import SimpleConfWxDialog
from config import config
from application import api
from gmusicapi.exceptions import AlreadyLoggedIn

class LoginFrame(SimpleConfWxDialog):
 def __init__(self, callback = lambda *args, **kwargs: None, args = [], kwargs = {}):
  self.callback = callback
  self.args = args
  self.kwargs = kwargs
  super(LoginFrame, self).__init__(config.login)
 
 def on_ok(self, event):
  """Try to login."""
  if super(LoginFrame, self).on_ok(event):
   uid = self.controls['uid'].GetValue()
   pwd = self.controls['pwd'].GetValue()
   remember = self.controls['remember'].GetValue()
   if not remember:
    self.section['uid'] = ''
    self.section['pwd'] = ''
   try:
    res = api.login(uid, pwd, api.FROM_MAC_ADDRESS)
   except AlreadyLoggedIn:
    return self.on_error('You are already logged in.')
   if not res:
    self.on_error('Failed to login.')
   else:
    self.callback(*self.args, **self.kwargs)
