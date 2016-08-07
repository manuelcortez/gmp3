"""The track menu."""

import wx, application
from functions.google import playlist_action, add_to_playlist, remove_from_playlist
from functions.util import do_login, format_track
from functions.sound import play, queue, unqueue
from functions.network import download_track
from db import session, Playlist
from showing import SHOWING_LIBRARY
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
  self.Bind(wx.EVT_MENU, application.frame.load_album, self.Append(wx.ID_ANY, 'Show A&lbum', 'Load the whole album.'))
  self.Bind(wx.EVT_MENU, self.add_to_library, self.Append(wx.ID_ANY, 'Add To &Library', 'Add the track to the library.'))
  self.Bind(wx.EVT_MENU, self.remove_from_library, self.Append(wx.ID_ANY, '&Remove From Library', 'Remove the track from the library.'))
  playlists_menu = wx.Menu()
  playlists = session.query(Playlist).all()
  if playlists:
   for p in playlists:
    self.Bind(wx.EVT_MENU, lambda event, playlist = p: add_to_playlist(playlist, self.track), playlists_menu.Append(wx.ID_ANY, '&%s' % p.name, p.description))
  self.Bind(wx.EVT_MENU, lambda event: Thread(target = playlist_action, args = ['Select a playlist to add this track to', 'Select a playlist', add_to_playlist, self.track]).start(), playlists_menu.Append(wx.ID_ANY, '&Remote...', 'Add this track to a remote playlist.'))
  self.AppendSubMenu(playlists_menu, '&Add To Playlist', 'Add this track to one of your playlists.')
  playlist_entries_menu = wx.Menu()
  entry_item = self.AppendSubMenu(playlist_entries_menu, '&Remove from playlist', 'Remove this track from one of your playlists.')
  if track.playlist_entries:
   for e in track.playlist_entries:
    self.Bind(wx.EVT_MENU, lambda event, entry = e: remove_from_playlist(e), playlist_entries_menu.Append(wx.ID_ANY, '&%s' % e.playlist.name, 'Remove this track from the %s playlist.' % e.playlist.name))
  else:
   entry_item.Enable(False)
  ratings_menu = wx.Menu()
  self.Bind(wx.EVT_MENU, lambda event: self.add_rating(0), ratings_menu.Append(wx.ID_ANY, '&Unthumb', 'Unrate the track.'))
  self.Bind(wx.EVT_MENU, lambda event: self.add_rating(1), ratings_menu.Append(wx.ID_ANY, 'Thumbs &Down', 'Thumbs down this track.'))
  self.Bind(wx.EVT_MENU, lambda event: self.add_rating(5), ratings_menu.Append(wx.ID_ANY, 'Thumbs &Up', 'Thumbs up this track.'))
  self.AppendSubMenu(ratings_menu, '&Rating', 'Rate the track.')
  download = self.Append(wx.ID_ANY, '&Downloaded' if track.downloaded else '&Download', 'Download %s.' % track)
  if track.downloaded:
   download.Enable(False)
  else:
   self.Bind(wx.EVT_MENU, self.download, download)
  self.Bind(wx.EVT_MENU, self.save_track, self.Append(wx.ID_ANY, '&Save Track...', 'Save the track to disk.'))
  self.Bind(wx.EVT_MENU, self.reload, self.Append(wx.ID_ANY, '&Reindex', 'Reindex the track from Google.'))
 
 def download(self, event, track = None):
  """Download was clicked."""
  if track is None:
   track = self.track
  try:
   url = application.api.get_stream_url(track.id)
  except NotLoggedIn:
   return do_login(callback = self.download, args = [event], kwargs = {'track': track})
  download_track(url, track.path)
 
 def save_track(self, event, path = None):
  """Save the track to disk."""
  if path is None:
   dlg = wx.FileDialog(None, message = 'Choose where to save the file', defaultFile = format_track(self.track) + '.mp3', style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
   if dlg.ShowModal() == wx.ID_OK:
    path = dlg.GetPath()
   dlg.Destroy()
  if path:
   try:
    download_track(application.api.get_stream_url(self.track.id), path)
   except NotLoggedIn:
    do_login(callback = self.save_track, args = [event], kwargs = dict(path = path))
  
 def add_rating(self, rating):
  """Rate the current track."""
  wx.MessageBox('Due to an error in the API ratings do not currently work.', 'Watch This Space', style = wx.ICON_EXCLAMATION)
 
 def add_to_library(self, event):
  """Add the current song to the library."""
  do_login(callback = application.api.add_store_track, args = [self.track.store_id])
  if application.frame.showing == SHOWING_LIBRARY:
   try:
    application.frame.remove_result(self.track)
   except ValueError:
    pass # It's not in the list after all.
   application.frame.add_results([self.track], clear = False)
 
 def remove_from_library(self, event):
  """Remove this track from the library."""
  do_login(callback = application.api.delete_songs, args = [self.track.id])
  if application.frame.showing == SHOWING_LIBRARY:
   application.frame.remove_result(self.track)
 
 def reload(self, event):
  """Reload the track from google."""
  try:
   self.track.populate(application.api.get_track_info(self.track.id))
  except NotLoggedIn:
   do_login(callback = self.reload, args = [event])
