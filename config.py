"""Configuration stuff."""

import application, os, os.path, wx, db
from wx.lib.filebrowsebutton import DirBrowseButton
from configobj import ConfigObj
from validate import Validator

config_dir = application.paths.GetUserDataDir()

def save():
 """Dump configuration to disk."""
 if not os.path.isdir(config_dir):
  os.makedirs(config_dir)
 config.write()

def make_dir_browser(dlg, label, value):
 """Create the control for the media directory selector."""
 ctrl = DirBrowseButton(dlg.panel, labelText = label)
 ctrl.SetValue(value)
 return ctrl

config = ConfigObj(os.path.join(config_dir, 'config.ini')) # The main configuration object.

# Create individual configuration sections:

# Login configuration.
config['login'] = config.get('login', {})
login_config = config['login']
login_config.title = 'Login'
spec = ConfigObj()
spec['uid'] = 'string(default = "")'
spec['pwd'] = 'string(default = "")'
spec['remember'] = 'boolean(default = True)'
login_config.configspec = spec
login_config.controls = {
 'pwd': lambda dlg, name, value: wx.TextCtrl(dlg.panel, value = value, style = wx.TE_PASSWORD)
}
login_config.names = {
 'uid': '&Username',
 'pwd': '&Password',
 'remember': '&Remember Credentials'
}

# Storage configuration.
config['storage'] = config.get('storage', {})
storage_config = config['storage']
storage_config.title = 'Storage'
spec = ConfigObj()
spec['media_dir'] = 'string(default = "%s")' % os.path.join(config_dir, 'media')
spec['quality'] = 'option("low", "med", "hi", default = "hi")'
spec['download'] = 'boolean(default = True)'
storage_config.configspec = spec
storage_config.names = {
 'media_dir': '&Media Directory',
 'quality': 'Audio &Quality',
 'download': '&Download tracks'
}

class QualityChoice(wx.Choice):
 def __init__(self, dlg, name, value):
  super(QualityChoice, self).__init__(dlg.panel, choices = ['hi', 'med', 'low'])
  self.SetValue(value)
 
 def GetValue(self):
  """Get the value of this control as a string."""
  return self.GetStringSelection()
 
 def SetValue(self, value):
  """Set the value of this control."""
  return self.SetStringSelection(value)

storage_config.controls = {
 'media_dir': make_dir_browser,
 'quality': QualityChoice
}

# Database configuration.
config['db'] = config.get('db', {})
db_config = config['db']
db_config.title = 'Database'
def db_config_updated():
 db.engine.echo = db_config['echo']
 application.frame.search_remote.SetValue(db_config['remote'])
db_config.config_updated = db_config_updated
spec = ConfigObj()
spec['url'] = 'string(default = "sqlite:///%s")' % os.path.join(config_dir, 'catalogue.db') # The URL for the database.
spec['echo'] = 'boolean(default = False)' # The echo argument for create_engine.
spec['remote'] = 'boolean(default = True)'
db_config.configspec = spec
db_config.names = {
 'url': 'Database &URL (Only change if you know what you\'re doing)',
 'echo': 'Enable Database &Debugging',
 'remote': 'Enable &Google Search'
}

# All configuration sections must be created above this line.
# 
# Add all configuration sections to the below list in the order they should appear in the Options menu.
sections = [
 login_config,
 storage_config,
 db_config
]

validator = Validator()
for section in config.sections:
 config.validate(validator, section = config[section])
