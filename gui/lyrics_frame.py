"""Provides a frame where you can edit the lyrics for a given track."""

import wx, application
from db import session
from functions.util import do_error


class LyricsFrame(wx.Frame):
    """Allows you to edit the lyrics for a track."""

    def __init__(self, track):
        self.track = track
        super(LyricsFrame, self).__init__(application.frame, title='Lyrics for %s - %s' % (track.artist, track.title))
        p = wx.Panel(self)
        s = wx.BoxSizer(wx.VERTICAL)
        self.lyrics = wx.TextCtrl(p, value=track.lyrics if track.lyrics is not None else '', style=wx.TE_RICH | wx.TE_MULTILINE)
        s.Add(self.lyrics, 1, wx.GROW)
        s1 = wx.BoxSizer(wx.HORIZONTAL)
        self.ok = wx.Button(p, label='&OK')
        self.ok.Bind(wx.EVT_BUTTON, self.on_ok)
        s1.Add(self.ok, 1, wx.GROW)
        self.cancel = wx.Button(p, label='&Cancel')
        self.cancel.Bind(wx.EVT_BUTTON, lambda event: self.Close(True))
        s1.Add(self.cancel, 1, wx.GROW)
        s.Add(s1, 0, wx.GROW)
        p.SetSizerAndFit(s)
        self.Show(True)
        self.Maximize()

    def on_ok(self, event):
        self.track.lyrics = self.lyrics.GetValue()
        session.add(self.track)
        try:
            session.commit()
            self.Close(True)
            if self.track is application.track:
                application.frame.update_lyrics(self.track)
        except Exception as e:
            do_error(e)
