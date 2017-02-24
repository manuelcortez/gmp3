"""Source menu."""

import webbrowser, wx, showing, application
from threading import Thread
from gmusicapi.exceptions import CallFailure, NotLoggedIn
from db import session, Track, URLStream
from config import config
from functions.util import do_login, do_error
from .base import BaseMenu
from .playlists import PlaylistsMenu
from .stations import StationsMenu
from server.base import app

class SourceMenu(BaseMenu):
 """The source menu."""
 def __init__(self, parent):
  self.name = '&Source'
  super(SourceMenu, self).__init__()
  parent.Bind(wx.EVT_MENU, lambda event: Thread(target = application.frame.load_library).start(), self.Append(wx.ID_ANY, '&Library\tCTRL+L', 'Load every song in your Google Music library.'))
  parent.Bind(wx.EVT_MENU, lambda event: Thread(target = application.frame.load_promoted_songs).start(), self.Append(wx.ID_ANY, 'Promoted &Songs\tCTRL+3', 'Load promoted songs.'))
  parent.Bind(wx.EVT_MENU, lambda event: application.frame.add_results(application.frame.queue, showing = showing.SHOWING_QUEUE), self.Append(wx.ID_ANY, '&Queue\tCTRL+SHIFT+Q', 'Show all tracks in the play queue.'))
  parent.Bind(wx.EVT_MENU, lambda event: application.frame.add_results(session.query(Track).all(), showing = showing.SHOWING_CATALOGUE), self.Append(wx.ID_ANY, '&Catalogue\tCTRL+0', 'Load all songs which are stored in the local database.'))
  parent.Bind(wx.EVT_MENU, lambda event: application.frame.add_results([x for x in session.query(Track).all() if x.downloaded is True], showing = showing.SHOWING_DOWNLOADED), self.Append(wx.ID_ANY, '&Downloaded\tCTRL+D', 'Show all downloaded tracks.'))
  self.AppendSubMenu(parent.playlists_menu if parent is application.frame else PlaylistsMenu(parent), '&Playlists', 'Select a local or remote playlist to view.')
  self.AppendSubMenu(parent.stations_menu if parent is application.frame else StationsMenu(parent), '&Radio Stations', 'Locally stored and remote radio stations.')
  parent.Bind(wx.EVT_MENU, lambda event: application.frame.add_results(session.query(URLStream), showing=showing.SHOWING_STREAMS), self.Append(wx.ID_ANY, '&Internet Streams\tCTRL+I', 'Show all internet streams.'))
  parent.Bind(wx.EVT_MENU, lambda event: setattr(application.frame, 'autoload', [application.frame.autoload[0]] if application.frame.autoload else []), self.Append(wx.ID_ANY, 'St&op Loading Results', 'Stop loading results to the track view.'))
  parent.Bind(wx.EVT_MENU, self.load_track, self.Append(wx.ID_ANY, 'Load Specific Track...\tCTRL+SHIFT+I', 'Load a track with a specific ID.'))
  parent.Bind(wx.EVT_MENU, lambda event: webbrowser.open('http://%s:%s@localhost:%d' % (config.http['uid'], config.http['pwd'], app.port)) if config.http['enabled'] else do_error('The web server is not running. Enable it and restart GMP.'), self.Append(wx.ID_ANY, '&Web Interface...', 'Load the web interface.'))
 
 def load_track(self, event, id = None):
  """Load a track by ID."""
  if id is None:
   dlg = wx.TextEntryDialog(application.frame, 'Enter the ID of the track to view', 'Track ID')
   if dlg.ShowModal() == wx.ID_OK:
    id = dlg.GetValue()
   else:
    id = None
   dlg.Destroy()
  if id is not None:
   try:
    info = application.api.get_track_info(id)
   except CallFailure:
    return do_error('Invalid track ID: %s.' % id)
   except NotLoggedIn:
    return do_login(callback = self.load_track, args = [event], kwargs = dict(id = id))
   application.frame.add_results([info], showing = 'ID: %s' % id)
