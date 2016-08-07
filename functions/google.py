"""Goele functions."""

import application, wx
from .util import do_login, do_error
from db import session, Playlist, PlaylistEntry
from gmusicapi.exceptions import NotLoggedIn
from threading import Thread

class PlaylistAction(object):
 """A playlist action to be performed once all playlists have been localised."""
 def __init__(self, message, title, callback, *args, **kwargs):
  """Initialise this action."""
  self.playlists = None # These will be set from within a thread most likely.
  self.message = message # The message for the resulting dialog.
  self.title = title # The title for the resulting dialog.
  self.callback = callback # The callback to be called.
  self.args = args # The arguments to call callback with.
  self.kwargs = kwargs # The keyword arguments to call callback with.
 
 def complete(self):
  """Call self.callback."""
  playlists = session.query(Playlist).all()
  dlg = wx.SingleChoiceDialog(application.frame, self.message, self.title, [x.name for x in playlists])
  if dlg.ShowModal() == wx.ID_OK:
   return self.callback(playlists[dlg.GetSelection()], *self.args, **self.kwargs)
  dlg.Destroy()

def playlist_action(message, title, callback, *args, **kwargs):
 """call callback with the resulting playlist as the first argument, followed by args and kwargs."""
 def localise_playlists(action):
  """Add all playlists to application.frame.playlists_to_localise."""
  try:
   action.playlists = application.api.get_all_user_playlist_contents()
  except NotLoggedIn:
   wx.CallAfter(do_login, callback = localise_playlists, args = [action])
 assert callable(callback), ' Callback must be callable.'
 application.frame.playlist_action = PlaylistAction(message, title, callback, *args, **kwargs)
 Thread(target = localise_playlists, args = [application.frame.playlist_action]).start()

def add_to_playlist(playlist, *tracks):
 """Add track to playlist."""
 application.frame.last_playlist = playlist
 playlist.tracks += tracks
 for pos, id in enumerate(application.api.add_songs_to_playlist(playlist.id, [x.id for x in tracks])):
  session.add(PlaylistEntry(id = id, playlist = playlist, track = tracks[pos]))
 session.commit()
 if application.frame.showing == playlist:
  application.frame.add_results(tracks, clear = False)

def remove_from_playlist(*entries):
 """Remove entry from playlist."""
 try:
  application.api.remove_entries_from_playlist([entry.id for entry in entries])
 except NotLoggedIn:
  return do_login(callback = remove_from_playlist, args = entries)
 for entry in entries:
  if application.frame.showing == entry.playlist:
   application.frame.remove_result(entry.track)
  session.delete(entry)
  entry.playlist.tracks.remove(entry.track)
 session.commit()

def delete_station(station):
 """Delete a station both from Google and the local database."""
 try:
  ids = application.api.delete_stations([station.id])
  if ids != [station.id]:
   do_error('Failed to delete the %s station.' % station.name)
  session.delete(station)
  if station in application.frame.stations:
   id, delete_id = application.frame.stations[station]
   application.frame.stations_menu.Delete(id)
   application.frame.delete_stations_menu.Delete(delete_id)
 except NotLoggedIn:
  do_login(callback = delete_station, args = [station])
