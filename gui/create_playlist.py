"""Creat playlists."""

import wx, application, six, logging
from wx.lib.sized_controls import SizedFrame
from gmusicapi.exceptions import NotLoggedIn
from wxgoodies.keys import add_accelerator
from db import session, Playlist, PlaylistEntry
from functions.util import do_error, do_login

logger = logging.getLogger(__name__)

class CreatePlaylist(SizedFrame):
 """A frame for creating playlists."""
 def __init__(self, name = '', description = '', public = False, tracks = []):
  """After creation will add all the tracks provided."""
  assert public in [True, False]
  assert isinstance(name, six.string_types)
  assert isinstance(description, six.string_types)
  assert isinstance(tracks, list)
  super(CreatePlaylist, self).__init__(None, title = 'Create Playlist')
  add_accelerator(self, 'ESCAPE', lambda event: self.Close(True))
  self.tracks = tracks
  p = self.GetContentsPane()
  wx.StaticText(p, label = '&Name')
  self.name = wx.TextCtrl(p, value = name, style = wx.TE_RICH2)
  wx.StaticText(p, label = '&Description')
  self.description = wx.TextCtrl(p, value = description, style = wx.TE_MULTILINE | wx.TE_RICH2)
  self.public = wx.CheckBox(p, label = '&Public')
  self.public.SetValue(public)
  l = '&Create'
  if self.tracks:
   l = '%s and add %s %s' % (l, len(self.tracks), 'track' if len(self.tracks) == 1 else 'tracks')
  self.done = wx.Button(p, label = l)
  self.done.SetDefault()
  self.done.Bind(wx.EVT_BUTTON, self.on_done)
 
 def on_done(self, event):
  """The done button was pressed."""
  name = self.name.GetValue()
  description = self.description.GetValue()
  public = self.public.GetValue()
  logger.debug('Attempting to create playlist with name "%s", description "%s" and public %s.', name, repr(description), public)
  if not name:
   do_error('Playlist names cannot be blank.')
   self.name.SetFocus()
  else:
   try:
    id = application.api.create_playlist(name, description, public)
    logger.debug('New playlist ID is %s.', id)
    p = Playlist(id = id, name = name, description = description)
    logger.debug('Created Playlist object %s.', p)
    session.add(p)
    application.frame.add_playlist(p)
    entry_ids = application.api.add_songs_to_playlist(p.id, [t.id for t in self.tracks])
    logger.debug('Entry IDs are: %s.', entry_ids)
    if len(entry_ids) == len(self.tracks):
     for pos, track in enumerate(self.tracks):
      p.tracks.append(track)
      e = PlaylistEntry(playlist = p, track = track, id = entry_ids[pos])
      logger.debug('Created playlist entry %s (%s).', e, e.track)
      session.add(e)
    else:
     do_error('Only %s %s out of %s were added to the playlist.' % (len(entry_ids), 'track' if len(entry_ids) == 1 else 'tracks', len(self.tracks)))
    session.commit()
    logger.debug('Done. Closing %s.', self)
    self.Close(True)
   except NotLoggedIn:
    do_login(callback = self.on_done, args = [event])
