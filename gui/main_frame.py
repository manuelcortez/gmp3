"""The main frame."""

from threading import Thread
import wx, application
from wxgoodies.keys import add_accelerator
from db import list_to_objects, session, Track
from config import save, db_config, sections
from sqlalchemy import func, or_
from configobj_dialog import ConfigObjDialog
from gmusicapi.exceptions import NotLoggedIn
from functions.util import do_login
from functions.sound import play

SEARCH_LABEL = '&Search'
SEARCHING_LABEL = '&Searching...'

class MainFrame(wx.Frame):
 """The main frame."""
 def __init__(self, *args, **kwargs):
  super(MainFrame, self).__init__(*args, **kwargs)
  p = wx.Panel(self)
  s = wx.BoxSizer(wx.VERTICAL)
  s1 = wx.BoxSizer(wx.HORIZONTAL)
  self.previous = wx.Button(p, label = '&Previous')
  self.play = wx.Button(p, label = '&Play')
  self.next = wx.Button(p, label = '&Next')
  self.search_label = wx.StaticText(p, label = SEARCH_LABEL)
  self.search = wx.TextCtrl(p, style = wx.TE_PROCESS_ENTER)
  self.search.Bind(wx.EVT_TEXT_ENTER, lambda event: self.do_remote_search() if self.search_remote.GetValue() else self.do_local_search())
  self.search_remote = wx.CheckBox(p, label = '&Google Search')
  self.search_remote.SetValue(db_config['remote'])
  s1.AddMany([
   (self.previous, 0, wx.GROW),
   (self.play, 0, wx.GROW),
   (self.next, 0, wx.GROW),
   (self.search_label, 0, wx.GROW),
   (self.search, 1, wx.GROW),
   (self.search_remote, 0, wx.GROW)
  ])
  s2 = wx.BoxSizer(wx.HORIZONTAL)
  vs = wx.BoxSizer(wx.VERTICAL)
  vs.Add(wx.StaticText(p, label = '&Tracks'), 0, wx.GROW)
  self.view = wx.ListBox(p)
  add_accelerator(self.view, 'RETURN', self.on_activate)
  self.view.SetFocus()
  vs.Add(self.view, 1, wx.GROW)
  ls = wx.BoxSizer(wx.VERTICAL)
  ls.Add(wx.StaticText(p, label = '&Lyrics'), 0, wx.GROW)
  self.lyrics = wx.TextCtrl(p, style = wx.TE_MULTILINE | wx.TE_READONLY)
  ls.Add(self.lyrics, 1, wx.GROW)
  s2.AddMany([
   (vs, 1, wx.GROW),
   (ls, 1, wx.GROW),
  ])
  s.AddMany([
   (s1, 0, wx.GROW),
   (s2, 1, wx.GROW)
  ])
  p.SetSizerAndFit(s)
  self.SetTitle()
  self.Bind(wx.EVT_CLOSE, self.on_close)
  mb = wx.MenuBar()
  self.options_menu = wx.Menu()
  for section in sections:
   self.Bind(wx.EVT_MENU, lambda event, section = section: ConfigObjDialog(section).Show(True), self.options_menu.Append(wx.ID_ANY, '&%s' % section.title))
  mb.Append(self.options_menu, '&Options')
  self.SetMenuBar(mb)
 
 def SetTitle(self, title = None):
  """Set the title to something."""
  if title is None:
   title = 'Not Playing'
  super(MainFrame, self).SetTitle('%s - %s' % (application.name, title))
 
 def add_result(self, result):
  """Add a result to the view."""
  self.view.Append(str(result))
  self.results.append(result)
 
 def add_results(self, results, clear = True, focus = True):
  """Add results to the view."""
  if clear:
   self.view.Clear()
   self.results = []
   for r in results:
    self.add_result(r)
   if focus:
    self.view.SetFocus()
 
 def do_remote_search(self):
  """Perform a search."""
  what = self.search.GetValue()
  def f(what):
   """Get the results and pass them onto f2."""
   try:
    results = [x['track'] for x in application.api.search(what)['song_hits']]
    def f2(results):
     """Clear the results queue and re-enable the search box."""
     self.search.Clear()
     self.add_results(list_to_objects(results))
     self.search_label.SetLabel(SEARCH_LABEL)
   except NotLoggedIn:
    def f2(results):
     """Get the user to login."""
     self.search_label.SetLabel(SEARCH_LABEL)
     do_login(callback = f, args = [what])
    results = []
   wx.CallAfter(f2, results)
  self.search_label.SetLabel(SEARCHING_LABEL)
  Thread(target = f, args = [what]).start()
 
 def do_local_search(self):
  """Perform a local search."""
  what = '%%%s%%' % self.search.GetValue()
  results = session.query(Track).filter(
   or_(
    func.lower(Track.title).like(what),
    func.lower(Track.artist).like(what),
    func.lower(Track.album).like(what)
   )
  ).all()
  self.add_results(results)
 
 def on_close(self, event):
  """Close the window."""
  db_config['remote'] = self.search_remote.GetValue()
  session.commit()
  save()
  event.Skip()
 
 def on_activate(self, event):
  """Enter was pressed on a track."""
  cr = self.view.GetSelection()
  if cr == -1:
   return wx.Bell()
  else:
   play(self.results[cr])
