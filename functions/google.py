"""Google functions."""

import application, wx, logging, six
from .util import do_login, do_error, load_station
from db import session, Playlist, PlaylistEntry
from showing import SHOWING_LIBRARY
from gmusicapi.exceptions import NotLoggedIn
from threading import Thread

logger = logging.getLogger(__name__)

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

def load_artist_tracks(artist):
 """Get all tracks for artist."""
 try:
  a = application.api.get_artist_info(artist.id)
  artist.populate(a)
  wx.CallAfter(application.frame.add_results, [], showing = artist)
  for album in a.get('albums', []):
   album = application.api.get_album_info(album['albumId'])
   wx.CallAfter(application.frame.add_results, album.get('tracks', []), clear = False)
 except NotLoggedIn:
  do_login(callback = load_artist_tracks, args = [artist])

def load_artist_top_tracks(artist):
 """Load the top tracks for artist."""
 a = application.api.get_artist_info(artist.id)
 wx.CallAfter(application.frame.add_results, a.get('topTracks', []), showing = '%s top tracks' % artist.name)

def artist_action(artists, callback, *args, **kwargs):
 """select an artist from artists and call callback(artist, *kwargs, **kwargs)."""
 do_login()
 def f1(artists):
  """Populate artists."""
  for a in artists:
   wx.CallAfter(a.populate, application.api.get_artist_info(a.id))
  wx.CallAfter(f2, artists)
 def f2(artists):
  """Make a dialog with the artist names."""
  if len(artists) == 1:
   artist = artists[0]
  else:
   dlg = wx.SingleChoiceDialog(application.frame, 'Select an artist', 'Multiple Artists', [x.name for x in artists])
   if dlg.ShowModal() == wx.ID_OK:
    artist = artists[dlg.GetSelection()]
   else:
    artist = None
   dlg.Destroy()
  if artist is not None:
   Thread(target = callback, args = [artist, *args], kwargs = kwargs).start()
 Thread(target = f1, args = [artists]).start()

def add_to_library(track):
 """Add track to the library."""
 try:
  track.id = application.api.add_store_track(track.store_id)
  session.add(track)
  session.commit()
  if application.frame.showing == SHOWING_LIBRARY:
   try:
    application.frame.remove_result(track)
   except ValueError:
    pass # It's not in the list after all.
   application.frame.add_results([track], clear = False)
 except NotLoggedIn:
  do_login(callback = add_to_library, args = [track])

def remove_from_library(track):
 """Remove track from the library."""
 try:
  application.api.delete_songs(track.id)
  track.id = track.store_id
  session.add(track)
  session.commit()
  if application.frame.showing == SHOWING_LIBRARY:
   application.frame.remove_result(track)
 except NotLoggedIn:
  do_login(callback = remove_from_library, args = [track])

def create_station(field, data, name = ''):
 """Creates a station with kwargs field = value."""
 logger.debug('Creating station with %s = %s.', field, data)
 assert isinstance(data, six.string_types), 'Invalid data: %s.' % data
 if not name:
  name = wx.GetTextFromUser('Enter the name for the new radio station', caption = 'Create Station')
 if name:
  id = application.api.create_station(name, **{field: data})
  s = load_station(dict(name = name, id = id))
  return s

def album_action(artist, callback, *args, **kwargs):
 """Perform an action on an album."""
 def f1(artist):
  """Get the albums for artist, and pass them onto f2."""
  wx.CallAfter(f2, application.api.get_artist_info(artist.id).get('albums', []))
 def f2(albums):
  """Build the dialog to choose an album."""
  if not albums:
   wx.CallAfter(do_error, 'There are no albums for this artist.')
  else:
   dlg = wx.SingleChoiceDialog(None, 'Select an album', 'Album Selection', ['%s (%s)' % (a.get('name', 'Unknown Album'), a['year']) for a in albums])
   if dlg.ShowModal() == wx.ID_OK:
    Thread(target = callback, args = [albums[dlg.GetSelection()]['albumId'], *args], kwargs = kwargs).start()
 Thread(target = f1, args = [artist]).start()
