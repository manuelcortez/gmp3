"""The main frame."""

from threading import Thread
import wx, application
from wxgoodies.keys import add_accelerator
from db import list_to_objects, session

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
  self.search.Bind(wx.EVT_TEXT_ENTER, self.do_search)
  self.search_remote = wx.CheckBox(p, label = '&Include Google Results')
  self.search_remote.SetValue(True)
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
 
 def SetTitle(self, title = None):
  """Set the title to something."""
  if title is None:
   title = 'Not Playing'
  super(MainFrame, self).SetTitle('%s - %s' % (application.name, title))
 
 def do_search(self, event):
  """Perform a search."""
  def f(what):
   """Get the results and pass them onto f2."""
   results = [x['track'] for x in application.api.search(what)['song_hits']]
   def f2(results):
    """Clear the results queue and re-enable the search box."""
    self.results = []
    self.search.Clear()
    self.view.Clear()
    for r in list_to_objects(results):
     self.results.append(r)
     self.view.Append(str(r))
    self.search_label.SetLabel(SEARCH_LABEL)
    self.view.SetFocus()
   wx.CallAfter(f2, results)
  self.search_label.SetLabel(SEARCHING_LABEL)
  Thread(target = f, args = [self.search.GetValue()]).start()
 
 def on_close(self, event):
  """Close the window."""
  session.commit()
  event.Skip()
 
 def on_activate(self, event):
  """Enter was pressed on a track."""
  cr = self.view.GetSelection()
  if cr == -1:
   return wx.Bell()
  wx.MessageBox('You pressed enter on %s.' % self.results[cr], 'Congratulations')
