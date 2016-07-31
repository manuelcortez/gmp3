"""Configuration stuff."""

import application, os, os.path, wx
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

# Database configuration.
config['db'] = {}
db_config = config['db']
db_config.title = 'Database'
spec = ConfigObj()
spec['url'] = 'string(default = "sqlite:///catalogue.db")' # The URL for the database.
spec['echo'] = 'boolean(default = False)' # The echo argument for create_engine.
spec['media_dir'] = 'string(default = "%s")' % os.path.join(config_dir, 'media')
db_config.configspec = spec
db_config.controls = {
 'media_dir': make_dir_browser
}
db_config.names = {
 'url': 'Database &URL (Only change if you know what you\'re doing)',
 'echo': 'Enable Database &Debugging',
 'media_dir': '&Media Directory'
}

config['login'] = {}
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

# All configuration sections must be created above this line.

validator = Validator()
for section in config.sections:
 config.validate(validator, section = config[section])
