"""A login frame."""

import wx
from configobj_dialog import ConfigObjDialog
from config import login_config
from application import api
from gmusicapi.exceptions import AlreadyLoggedIn

class LoginFrame(ConfigObjDialog):
 def __init__(self, callback = lambda *args, **kwargs: None, args = [], kwargs = {}):
  self.callback = callback
  self.args = args
  self.kwargs = kwargs
  super(LoginFrame, self).__init__(login_config)
 
 def handle_validation_errors(self, res):
  """Try to login."""
  uid = self.controls['uid'].GetValue()
  pwd = self.controls['pwd'].GetValue()
  remember = self.controls['remember'].GetValue()
  if not remember:
   self.section['uid'] = ''
   self.section['pwd'] = ''
  try:
   res = api.login(uid, pwd, api.FROM_MAC_ADDRESS)
  except AlreadyLoggedIn:
   return wx.MessageBox('You are already logged in.', 'Error', style = wx.ICON_EXCLAMATION)
  if not res:
   wx.MessageBox('Failed to login', 'Error', style = wx.ICON_EXCLAMATION)
  else:
   self.callback(*self.args, **self.kwargs)
   return super(LoginFrame, self).handle_validation_errors(res)
