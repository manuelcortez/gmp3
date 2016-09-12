"""Track menu."""

import wx, application
from .base import BaseMenu
from functions.google import playlist_action, add_to_playlist

class TrackMenu(BaseMenu):
 """The track menu."""
 def __init__(self, parent):
  self.name = '&Track'
  super(TrackMenu, self).__init__()
  parent.Bind(wx.EVT_MENU, application.frame.select_playing, self.Append(wx.ID_ANY, '&Focus Playing\tALT+RETURN', 'Select the currently playing result.'))
  parent.Bind(wx.EVT_MENU, application.frame.load_artist_tracks, self.Append(wx.ID_ANY, 'Goto &Artist\tCTRL+4', 'View all tracks by the artist of the currently focused track.'))
  parent.Bind(wx.EVT_MENU, application.frame.load_related_artist, self.Append(wx.ID_ANY, 'Go To &Related Artist...\tCTRL+7', 'Select an artist related to the artist of the currently selected result.'))
  parent.Bind(wx.EVT_MENU, application.frame.load_current_album, self.Append(wx.ID_ANY, 'Go To A&lbum\tCTRL+5', 'Load the album of the currently selected track.'))
  parent.Bind(wx.EVT_MENU, application.frame.load_album, self.Append(wx.ID_ANY, '&Choose Album\tCTRL+6', 'Choose an album from the artist of the currently selected artist.'))
  parent.Bind(wx.EVT_MENU, application.frame.load_top_tracks, self.Append(wx.ID_ANY, '&Top Tracks\tCTRL+;', 'Load the top tracks for the artist of the currently selected track.'))
  parent.Bind(wx.EVT_MENU, application.frame.toggle_library, self.Append(wx.ID_ANY, 'Add / Remove From &Library\tCTRL+/', 'Add or remove the currently selected track from library.'))
  parent.Bind(wx.EVT_MENU, lambda event: playlist_action('Select a playlist to add this track to', 'Select A Playlist', add_to_playlist, application.frame.get_result()) if application.frame.get_result() is not None else wx.Bell(), self.Append(wx.ID_ANY, 'Add To &Playlist...\tCTRL+8', 'Add the currently selected track to a playlist.'))
  parent.Bind(wx.EVT_MENU, lambda event: add_to_playlist(application.frame.last_playlist, application.frame.get_result()) if application.frame.last_playlist is not None and application.frame.application.frame.get_result() is not None else wx.Bell(), self.Append(wx.ID_ANY, 'Add To Most Recent Playlist\tCTRL+RETURN', 'Add the currently selected track to the most recent playlist.'))
  parent.Bind(wx.EVT_MENU, application.frame.do_delete, self.Append(wx.ID_ANY, '&Delete\tDELETE', 'Delete the currently selected track from the current view.'))
  parent.Bind(wx.EVT_MENU, self.copy_id, self.Append(wx.ID_ANY, '&Copy ID\tCTRL+SHIFT+C', 'Copy the ID of the current track to the clipboard.'))
 
 def copy_id(self, event):
  """Copy the ID of the current track to the clipboard."""
  cr = application.frame.get_result()
  if cr is None:
   wx.Bell()
  else:
   application.frame.do_copy_id(cr)
