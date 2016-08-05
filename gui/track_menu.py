"""The track menu."""

import wx, application
from functions.google import playlist_action, add_to_playlist
from functions.util import do_login
from functions.sound import play, queue, unqueue
from functions.network import download_track
from db import session, Playlist
from gmusicapi.exceptions import NotLoggedIn
from threading import Thread

class TrackMenu(wx.Menu):
 def __init__(self, track):
  """Initialise with a track to populate the menu."""
  super(TrackMenu, self).__init__()
  self.track = track
  self.Bind(wx.EVT_MENU, lambda event: play(track), self.Append(wx.ID_ANY, '&Play', 'Play %s.' % track))
  self.Bind(wx.EVT_MENU, lambda event: queue(track), self.Append(wx.ID_ANY, '&Queue Track', 'Add %s to the play queue.' % track))
  unqueue_item = self.Append(wx.ID_ANY, '&Unqueue Track', 'Remove the track from the play queue.')
  self.Bind(wx.EVT_MENU, lambda event: unqueue(track), unqueue_item)
  unqueue_item.Enable(track in application.frame.queue)
  download = self.Append(wx.ID_ANY, '&Downloaded' if track.downloaded else '&Download', 'Download %s.' % track)
  if track.downloaded:
   download.Enable(False)
  else:
   self.Bind(wx.EVT_MENU, self.download, download)
  self.Bind(wx.EVT_MENU, self.save_track, self.Append(wx.ID_ANY, '&Save Track...', 'Save the track to disk.'))
  playlists_menu = wx.Menu()
  playlists = session.query(Playlist).all()
  if playlists:
   for p in playlists:
    self.Bind(wx.EVT_MENU, lambda event, playlist = p: add_to_playlist(playlist, self.track), playlists_menu.Append(wx.ID_ANY, '&%s' % p.name, p.description))
  self.Bind(wx.EVT_MENU, lambda event: Thread(target = playlist_action, args = ['Select a playlist to add this track to', 'Select a playlist', add_to_playlist, self.track]).start(), playlists_menu.Append(wx.ID_ANY, '&Remote', 'Add this track to a remote playlist.'))
  self.AppendSubMenu(playlists_menu, '&Add To Playlist', 'Add this track to one of your playlists.')
 
 def download(self, event, track = None):
  """Download was clicked."""
  if track is None:
   track = self.track
  try:
   url = application.api.get_stream_url(track.id)
  except NotLoggedIn:
   return do_login(callback = self.download, args = [event], kwargs = {'track': track})
  download_track(url, track.path)
 
 def save_track(self, event):
  """Save the track to disk."""
  