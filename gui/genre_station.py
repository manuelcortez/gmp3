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
  self.genres = []
  wx.StaticText(p, label = '&Genres')
  self.main_genre = wx.ListBox(p, choices = [x['name'] for x in self.genres])
  self.main_genre.Bind(wx.EVT_LISTBOX, self.update_sub_genres)
  self.main_genre.Bind(wx.EVT_LISTBOX, self.update_name)
  do_login(callback = self.update_genres, args = [None])
  wx.StaticText(p, label = '&Sub Genre')
  self.sub_genre = wx.ListBox(p)
  self.sub_genre.Bind(wx.EVT_LISTBOX, self.update_name)
  self.ok = wx.Button(p, label = '&OK')
  self.ok.SetDefault()
  self.ok.Bind(wx.EVT_BUTTON, self.on_ok)
  wx.Button(p, label = '&Cancel').Bind(wx.EVT_BUTTON, lambda event: self.Close(True))
 
 def update_genres(self, event):
  """Update the main genre list."""
  self.main_genre.Clear()
  self.genres = application.api.get_genres()
  self.main_genre.AppendItems([x['name'] for x in self.genres])
 
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
 
 def update_sub_genres(self, event):
  """Update the sub genres list."""
  g = self.get_main_genre()
  if g is not None:
   self.sub_genre.Clear()
   print('Genre is %s.' % g)
   self.sub_genre.AppendItems([x.replace('_', ' ') for x in g.get('children', [])])
 
 def update_name(self, event):
  """Update the name field according to the contents of the two genre boxes."""
  sub = self.get_sub_genre()
  if sub is None:
   main = self.get_main_genre()
   if main is None:
    name = 'Nothing'
   else:
    print(main.keys())
    name = main['name']
  else:
   name = sub
  self.name.SetValue('Genre station for %s' % name.replace('_', ' '))
 
 def on_ok(self, event):
  """The OK button was pressed."""
  do_error('You chose %s.' % self.get_sub_genre())
