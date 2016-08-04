"""The track menu."""

import wx, application
from functions.util import do_login
from functions.sound import play, queue
from functions.network import download_track
from gmusicapi.exceptions import NotLoggedIn

class TrackMenu(wx.Menu):
 def __init__(self, track):
  """Initialise with a track to populate the menu."""
  super(TrackMenu, self).__init__()
  self.track = track
  self.Bind(wx.EVT_MENU, lambda event: play(track), self.Append(wx.ID_ANY, '&Play', 'Play %s.' % track))
  self.Bind(wx.EVT_MENU, lambda event: queue(track), self.Append(wx.ID_ANY, 'Add to &Queue', 'Add %s to the play queue.' % track))
  download = self.Append(wx.ID_ANY, '&Downloaded' if track.downloaded else '&Download', 'Download %s.' % track)
  if track.downloaded:
   download.Enable(False)
  else:
   self.Bind(wx.EVT_MENU, self.download, download)
 
 def download(self, event, track = None):
  """Download was clicked."""
  if track is None:
   track = self.track
  try:
   url = application.api.get_stream_url(track.id)
  except NotLoggedIn:
   return do_login(callback = self.download, args = [event], kwargs = {'track': track})
  download_track(url, track.path)
