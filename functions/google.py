"""Goele functions."""

import application, wx
from .util import do_login, load_playlist, do_error
from db import session, PlaylistEntry
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
