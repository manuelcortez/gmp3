"""Provides the InternetStreamFrame class."""

import wx, logging
from wx.lib.sized_controls import SizedFrame
from db import URLStream, session
from functions.util import do_error

logger = logging.getLogger(__name__)

class InternetStreamFrame(SizedFrame):
 """Adds a new internet stream."""
 def __init__(self, stream=None):
  """Initialise with a stream to edit the stream instead of creating a new one."""
  super(InternetStreamFrame, self).__init__(None, title='Add Stream' if stream is None else 'Edit Stream')
  if stream is None:
   self.stream = URLStream()
  else:
   self.stream = stream
  p = self.GetContentsPane()
  p.SetSizerType('form')
  wx.StaticText(p, label='&Name')
  self.name = wx.TextCtrl(p, value=self.stream.name or '', style=wx.TE_RICH)
  wx.StaticText(p, label='&URL')
  self.url = wx.TextCtrl(p, value=self.stream.url or '', style=wx.TE_RICH)
  self.ok = wx.Button(p, label='&OK')
  self.ok.Bind(wx.EVT_BUTTON, self.on_ok)
  self.ok.SetDefault()
  self.cancel = wx.Button(p, label='&Cancel')
  self.cancel.Bind(wx.EVT_BUTTON, lambda event: self.Close(True))
  self.Show(True)
  self.Maximize()

 def on_ok(self, event):
  """OK button was pressed."""
  name = self.name.GetValue()
  url = self.url.GetValue()
  if not name:
   do_error('You must supply a name.')
   self.name.SetFocus()
  elif not url:
   do_error('You must specify a URL.')
   self.url.SetFocus()
  else:
   self.stream.name = name
   self.stream.url = url
   session.add(self.stream)
   session.commit()
   logger.info('Committed %r.', self.stream)
   self.Close(True)
