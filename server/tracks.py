"""Track-related routes."""

import wx, application, config
from functions.sound import play, queue, get_previous, get_next, set_volume
from db import session, Track, Playlist, Station
from .base import app, jsonify, NotFound
from sqlalchemy.orm.exc import NoResultFound

class storage(object):
 """Store queries for get_info."""
 playlists = []
 stations = []
 tracks = []
 now_playing = None
 previous = None
 next = None
 play_pause = None

track_actions = {
 'previous': lambda: play(get_previous()),
 'next': lambda: play(get_next()),
 'play_pause': lambda: application.frame.play_pause(None),
 'volume_down': lambda: set_volume(max(0, application.frame.volume.GetValue() - 5)),
 'volume_up': lambda: set_volume(min(100, application.frame.volume.GetValue() + 5))
}

@app.route('/play_track/<key>')
def play_track(request, key):
 """Play the track with the given ID."""
 def f(key):
  try:
   track = session.query(Track).filter(Track.key == key).one()
   play(track)
  except NoResultFound:
   pass # No track with that id.
 wx.CallAfter(f, key)
 return jsonify(
  {
   'action': 'play',
   'track': key
  }
 )

@app.route('/queue_track/<id>')
def queue_track(request, id):
 """Queue the track with the given ID."""
 def f(id):
  try:
   track = session.query(Track).filter(Track.key == id).one()
   queue(track)
  except NoResultFound:
   pass # No track with that id.
 wx.CallAfter(f, id)
 return jsonify(
  {
   'action': 'queue',
   'track': id
  }
 )

@app.route('/info', protected = False)
def get_info(request):
 """Get all the playlists, radio stations and tracks in the player."""
 return jsonify(
  {
   'playlists': storage.playlists,
   'stations': storage.stations,
   'tracks': storage.tracks,
   'now_playing': storage.now_playing,
   'previous': storage.previous,
   'next': storage.next,
   'volume': config.config.system['volume'],
   'play_pause': storage.play_pause
  }
 )

@app.route('/track/<action>')
def action(request, action):
 """Perform an action on tracks."""
 if action in track_actions:
  wx.CallAfter(track_actions[action])
  return jsonify(
   {
    'action': action
   }
  )
 else:
  raise NotFound('No such action: %s.' % action)

@app.route('/playlist/<key>')
def show_playlist(request, key):
 """Load the playlist into the GUI."""
 def f(key):
  """Actually perform the load."""
  try:
   playlist = session.query(Playlist).filter(Playlist.key == key).one()
   application.frame.add_results(playlist.tracks, showing = playlist)
  except NoResultFound:
   pass # No matter.
 wx.CallAfter(f, key)
 return jsonify(
  {
   'action': 'playlist',
   'playlist': key
  }
 )

@app.route('/station/<key>')
def show_station(request, key):
 """Load a station into the GUI."""
 def f(key):
  try:
   station = session.query(Station).filter(Station.key == key).one()
   application.frame.load_station(station)
  except NoResultFound:
   pass # No worries.
 wx.CallAfter(f, key)
 return jsonify(
  {
   'action': 'station',
   'station': key
  }
 )

@app.route('/search/<string>')
def do_search(request, string):
 """Perform a search."""
 def f(string):
  """Search for string."""
  application.frame.do_local_search(string) if application.frame.offline_search.IsChecked() else application.frame.do_remote_search(string)
 wx.CallAfter(f, string)
 return jsonify(
  {
   'action': 'search',
   'string': string
  }
 )

@app.route('/volume/<value>')
def volume(request, value):
 """Set the player volume."""
 try:
  volume = int(value)
 except ValueError:
  return jsonify(
   {
    'error': 'Could not convert %r to an integer.' % value
   }
  )
 volume = min(100, volume)
 volume = max(volume, 0)
 wx.CallAfter(set_volume, volume)
 return jsonify(
  {
   'action': 'set_volume',
   'value': volume
  }
 )