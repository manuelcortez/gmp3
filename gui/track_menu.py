"""The track menu."""

import wx, application
from functions.google import playlist_action, add_to_playlist, remove_from_playlist, add_to_library, remove_from_library
from functions.util import do_login, format_track, do_error
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
  self.Bind(wx.EVT_MENU, application.frame.load_artist_tracks, self.Append(wx.ID_ANY, 'Show A&rtist', 'Load all artist tracks.'))
  self.Bind(wx.EVT_MENU, application.frame.load_related_artist, self.Append(wx.ID_ANY, '&Related Artists...', 'Load a related artist.'))
  self.Bind(wx.EVT_MENU, application.frame.load_album, self.Append(wx.ID_ANY, 'Show A&lbum', 'Load the whole album.'))
  self.Bind(wx.EVT_MENU, application.frame.load_top_tracks, self.Append(wx.ID_ANY, 'Show Artist &Top Tracks', 'Load an artist\'s top tracks.'))
  self.Bind(wx.EVT_MENU, self.toggle_library, self.Append(wx.ID_ANY, '%s &Library' % ('Remove From' if track.in_library else 'Add to'), 'Add the track to the library.'))
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
  if self.track.in_library:
   do_error('To rate this track first add it to your library.')
  else:
   application.api.change_song_metadata({'id': self.track.id, 'rating': str(rating)})
 
 def reload(self, event):
  """Reload the track from google."""
  try:
   self.track.populate(application.api.get_track_info(self.track.id))
  except NotLoggedIn:
   do_login(callback = self.reload, args = [event])
 
 def toggle_library(self, event):
  """If self.track is in the library, remove it, otherwise add it."""
  if self.track.in_library:
   remove_from_library(self.track)
  else:
   add_to_library(self.track)
