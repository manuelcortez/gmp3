from config import application, config, wx
from wx.lib.sized_controls import SizedFrame
from configobj_dialog import ConfigObjDialog

class ConfigFrame(SizedFrame):
 def __init__(self):
  super(ConfigFrame, self).__init__(None, title = 'Configuration Test')
  p = self.GetContentsPane()
  p.SetSizerType('vertical')
  for s in config.sections:
   b = wx.Button(p, label = '&%s' % s)
   b.Bind(wx.EVT_BUTTON, lambda event, name = s: ConfigObjDialog(config[name]).Show(True))

if __name__ == '__main__':
 f = ConfigFrame()
 f.Show(True)
 f.Maximize()
 application.app.MainLoop()
