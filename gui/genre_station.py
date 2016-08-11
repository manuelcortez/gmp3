"""Genre Stations."""

import application, wx
from wx.lib.sized_controls import SizedFrame
from wxgoodies.keys import add_accelerator
from functions.google import create_station
from functions.util import do_login, do_error

class GenreStation(SizedFrame):
 """A frame for creating genre stations."""
 def __init__(self):
  super(GenreStation, self).__init__(None, title = 'Create A Genre Station')
  add_accelerator(self, 'ESCAPE', lambda event: self.Close(True))
  p = self.GetContentsPane()
  wx.StaticText(p, label = '&Name')
  self.name = wx.TextCtrl(p, style = wx.TE_RICH2)
  self.genres = [] # The ids for add_station.
  wx.StaticText(p, label = '&Genre')
  self.genre = wx.ListBox(p)
  self.genre.Bind(wx.EVT_LISTBOX, self.update_name)
  do_login(callback = self.update_genres)
  self.ok = wx.Button(p, label = '&OK')
  self.ok.SetDefault()
  self.ok.Bind(wx.EVT_BUTTON, self.on_ok)
  wx.Button(p, label = '&Cancel').Bind(wx.EVT_BUTTON, lambda event: self.Close(True))
 
 def update_genres(self):
  """Update the main genre list."""
  self.genre.Clear()
  for g in application.api.get_genres():
   self.genres.append(g['id'])
   self.genre.Append(g['name'])
   for c in g.get('children', []):
    self.genres.append(c)
    self.genre.Append(c.replace('_', ' '))
 
 def get_main_genre(self):
  """Get the main genre."""
  cr = self.main_genre.GetSelection()
  if cr != -1:
   return self.genres[cr]
 
 def get_sub_genre(self):
  """Get the sub genre."""
  g = self.get_main_genre()
  if g is None:
   return g
  cr = self.sub_genre.GetSelection()
  if cr == -1:
   return g['id']
  else:
   return g['children'][cr]
 
 def update_name(self, event):
  """Update the name field according to the contents of the two genre boxes."""
  self.name.SetValue('Genre station for %s' % self.genre.GetStringSelection())
 
 def on_ok(self, event):
  """The OK button was pressed."""
  cr = self.genre.GetSelection()
  if cr == -1:
   do_error('You must select a genre to seed from.')
  else:
   genre = self.genres[cr]
   name = self.name.GetValue()
   if name:
    s = create_station('genre_id', genre, name = name)
    if name is not None:
     application.frame.load_station(s)
    self.Close(True)
   else:
    do_error('You must provide a name.')
