"""The main frame."""

from threading import Thread
import wx, application
from wxgoodies.keys import add_accelerator
from db import list_to_objects, session, Track
from config import save, system_config, sections
from sqlalchemy import func, or_
from configobj_dialog import ConfigObjDialog
from gmusicapi.exceptions import NotLoggedIn
from functions.util import do_login
from functions.sound import play, get_previous, get_next

SEARCH_LABEL = '&Search'
SEARCHING_LABEL = '&Searching...'
PLAY_LABEL = '&Play'
PAUSE_LABEL = '&Pause'

class MainFrame(wx.Frame):
 """The main frame."""
 def __init__(self, *args, **kwargs):
  super(MainFrame, self).__init__(*args, **kwargs)
  self.queue = [] # The play queue.
  self.results = []
  p = wx.Panel(self)
  s = wx.BoxSizer(wx.VERTICAL)
  s1 = wx.BoxSizer(wx.HORIZONTAL)
  self.previous = wx.Button(p, label = '&Previous')
  self.play = wx.Button(p, label = PLAY_LABEL)
  self.play.Bind(wx.EVT_BUTTON, self.play_pause)
  self.next = wx.Button(p, label = '&Next')
  self.search_label = wx.StaticText(p, label = SEARCH_LABEL)
  self.search = wx.TextCtrl(p, style = wx.TE_PROCESS_ENTER)
  self.search.Bind(wx.EVT_TEXT_ENTER, lambda event: self.do_local_search(self.search.GetValue()) if self.offline_search.IsChecked() else self.do_remote_search(self.search.GetValue()))
  s1.AddMany([
   (self.previous, 0, wx.GROW),
   (self.play, 0, wx.GROW),
   (self.next, 0, wx.GROW),
   (self.search_label, 0, wx.GROW),
   (self.search, 1, wx.GROW)
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
  s3 = wx.BoxSizer(wx.HORIZONTAL)
  s3.Add(wx.StaticText(p, label = '&Volume'), 0, wx.GROW)
  self.volume = wx.Slider(p, value = system_config['volume'], style = wx.SL_VERTICAL)
  self.volume.Bind(wx.EVT_SLIDER, lambda event: self.update_volume(self.volume.GetValue()))
  self.update_volume(system_config['volume'])
  s3.Add(self.volume, 1, wx.GROW)
  s3.Add(wx.StaticText(p, label = '&Position'), 0, wx.GROW)
  self.position= wx.Slider(p, style = wx.SL_HORIZONTAL)
  self.position.Bind(wx.EVT_SLIDER, lambda event: application.stream.set_position((int(application.stream.get_length() / 100) * self.position.GetValue())) if application.stream else None)
  self.position_timer = wx.Timer(self)
  self.Bind(wx.EVT_TIMER, self.play_manager, self.position_timer)
  self.position_timer.Start(10)
  s.AddMany([
   (s1, 0, wx.GROW),
   (s2, 1, wx.GROW),
   (s3, 0, wx.GROW),
  ])
  p.SetSizerAndFit(s)
  self.SetTitle()
  self.Bind(wx.EVT_CLOSE, self.on_close)
  mb = wx.MenuBar()
  fm = wx.Menu() # File menu.
  self.offline_search = fm.AppendCheckItem(wx.ID_ANY, '&Offline Search', 'Search the local database rather than google')
  self.offline_search.Check(system_config['offline_search'])
  self.Bind(wx.EVT_MENU, lambda event: self.Close(True), fm.Append(wx.ID_EXIT, '&Quit', 'Exit the program.'))
  mb.Append(fm, '&File')
  pm = wx.Menu() # Play menu.
  self.Bind(wx.EVT_MENU, self.play_pause, pm.Append(wx.ID_ANY, '&Play / Pause', 'Play or pause the current track.'))
  self.Bind(wx.EVT_MENU, lambda event: self.update_volume(max(0, self.volume.GetValue() - 5)), pm.Append(wx.ID_ANY, 'Volume &Down\tCTRL+DOWN', 'Reduce volume by 5%.'))
  self.Bind(wx.EVT_MENU, lambda event: self.update_volume(min(100, self.volume.GetValue() + 5)), pm.Append(wx.ID_ANY, 'Volume &Up\tCTRL+UP', 'Increase volume by 5%.'))
  mb.Append(pm, '&Play')
  self.options_menu = wx.Menu()
  for section in sections:
   self.Bind(wx.EVT_MENU, lambda event, section = section: ConfigObjDialog(section).Show(True), self.options_menu.Append(wx.ID_ANY, '&%s' % section.title, 'Edit the %s configuration.' % section.title))
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
   if clear:
    self.update_labels()
 
 def do_remote_search(self, what):
  """Perform a searchon Google Play Music for what."""
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
 
 def do_local_search(self, what):
  """Perform a local search for what."""
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
  self.position_timer.Stop()
  if application.stream:
   application.stream.stop()
  system_config['offline_search'] = self.offline_search.IsChecked()
  system_config['volume'] = self.volume.GetValue()
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
 
 def update_volume(self, value):
  """Update the volume of the main output."""
  self.volume.SetValue(value)
  application.output.set_volume(value)
 
 def update_labels(self):
  """Update the labels of the previous and next buttons."""
  prev = get_previous()
  self.previous.SetLabel('&Previous' if prev is None else '&Previous (%s)' % prev)
  next = get_next(remove = False)
  self.next.SetLabel('&Next' if next is None else '&Next (%s)' % next)
 
 def play_manager(self, event):
  """Manage the currently playing track."""
  if application.stream:
   pos = application.stream.get_position()
   length = application.stream.get_length()
   if not self.position.HasFocus():
    self.position.SetValue(int(pos * (100 / length)))
   if pos == length:
    play(get_next(remove = True))
  else:
   self.position.SetValue(0)
 
 def play_pause(self, event):
  """Play or pause the current track."""
  if application.stream:
   if application.stream.is_paused:
    application.stream.play()
    self.play.SetLabel(PAUSE_LABEL)
   else:
    application.stream.pause()
    self.play.SetLabel(PLAY_LABEL)
  else:
   wx.Bell()
