"""Stations menu."""

import wx, application
from functions.google import delete_station
from db import Station, session

class StationsMenu(wx.Menu):
 """A menu to hold all local radio stations."""
 def __init__(self, parent, add_stations = True):
  self.parent = parent
  super(StationsMenu, self).__init__()
  parent.Bind(wx.EVT_MENU, application.frame.load_remote_station, self.Append(wx.ID_ANY, '&Remote...%s' % ('\tCTRL+2' if parent is application.frame else ''), 'Load a radio station from Google.'))
  self.delete_menu = wx.Menu()
  if add_stations:
   for s in session.query(Station).order_by(Station.name.desc()).all():
    self.add_station(s)
 
 def add_station(self, station, id = wx.ID_ANY, delete_id = wx.ID_ANY):
  """Add a station to this menu."""
  self.parent.Bind(wx.EVT_MENU, lambda event, station = station: application.frame.load_station(station), self.Insert(0, id, '&%s' % station.name, 'Load the %s station.' % station.name))
  self.parent.Bind(wx.EVT_MENU, lambda event, station = station: delete_station(station) if wx.MessageBox('Are you sure you want to delete the %s station?' % station.name, 'Are You Sure?', style = wx.ICON_QUESTION | wx.YES_NO) == wx.YES else None, self.delete_menu.Insert(0, delete_id, '&%s...' % station.name, 'Delete the %s station.' % station.name))
