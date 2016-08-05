"""Goele functions."""

import application, wx
from .util import do_login, load_playlist
from gmusicapi.exceptions import NotLoggedIn

def localise_playlists(playlists):
 """Localise all playlists."""
 for p in playlists:
  yield load_playlist(p)

def playlist_action(message, title, callback, *args, **kwargs):
 """call callback with the resulting playlist as the first argument, followed by args and kwargs."""
 def select_playlist(message, title, playlists):
  """Get the contents of the right playlist."""
  playlists = list(localise_playlists(playlists))
  dlg = wx.SingleChoiceDialog(application.frame, message, title, [x.name for x in playlists])
  if dlg.ShowModal() == wx.ID_OK:
   callback(playlists[dlg.GetSelection()], *args, **kwargs)
  dlg.Destroy()
 try:
  wx.CallAfter(select_playlist, message, title, application.api.get_all_user_playlist_contents())
 except NotLoggedIn:
  do_login(callback = playlist_action, args = [message, title, callback, *args], kwargs = kwargs)

def add_to_playlist(playlist, *tracks):
 """Add track to playlist."""
 playlist.tracks += tracks
 application.api.add_songs_to_playlist(playlist.id, [x.id for x in tracks])
