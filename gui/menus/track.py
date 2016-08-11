"""Track menu."""

import wx
from .base import BaseMenu
from functions.google import playlist_action, add_to_playlist

class TrackMenu(BaseMenu):
 """The track menu."""
 def __init__(self, frame):
  self.name = '&Track'
  self.frame = frame
  super(TrackMenu, self).__init__()
  frame.Bind(wx.EVT_MENU, frame.select_playing, self.Append(wx.ID_ANY, '&Focus Playing\tALT+RETURN', 'Select the currently playing result.'))
  frame.Bind(wx.EVT_MENU, frame.load_artist_tracks, self.Append(wx.ID_ANY, 'Goto &Artist\tCTRL+4', 'View all tracks by the artist of the currently focused track.'))
  frame.Bind(wx.EVT_MENU, frame.load_related_artist, self.Append(wx.ID_ANY, 'Go To &Related Artist...\tCTRL+7', 'Select an artist related to the artist of the currently selected result.'))
  frame.Bind(wx.EVT_MENU, frame.load_current_album, self.Append(wx.ID_ANY, 'Go To A&lbum\tCTRL+5', 'Load the album of the currently selected track.'))
  frame.Bind(wx.EVT_MENU, frame.load_album, self.Append(wx.ID_ANY, '&Choose Album\tCTRL+6', 'Choose an album from the artist of the currently selected artist.'))
  frame.Bind(wx.EVT_MENU, frame.load_top_tracks, self.Append(wx.ID_ANY, '&Top Tracks\tCTRL+;', 'Load the top tracks for the artist of the currently selected track.'))
  frame.Bind(wx.EVT_MENU, frame.toggle_library, self.Append(wx.ID_ANY, 'Add / Remove From &Library\tCTRL+/', 'Add or remove the currently selected track from library.'))
  frame.Bind(wx.EVT_MENU, lambda event: playlist_action('Select a playlist to add this track to', 'Select A Playlist', add_to_playlist, frame.get_result()) if frame.get_result() is not None else wx.Bell(), self.Append(wx.ID_ANY, 'Add To &Playlist...\tCTRL+8', 'Add the currently selected track to a playlist.'))
  frame.Bind(wx.EVT_MENU, lambda event: add_to_playlist(frame.last_playlist, frame.get_result()) if frame.last_playlist is not None and frame.frame.get_result() is not None else wx.Bell(), self.Append(wx.ID_ANY, 'Add To Most Recent Playlist\tCTRL+RETURN', 'Add the currently selected track to the most recent playlist.'))
