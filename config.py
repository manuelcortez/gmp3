"""Configuration stuff."""

import application, os, os.path, wx
from wx.lib.filebrowsebutton import DirBrowseButton
from configobj import ConfigObj
from validate import Validator
from gui.widgets import StringChoice, FloatSpin

config_dir = application.paths.GetUserLocalDataDir()

def create_config_dir():
 """Create the configuration directory."""
 if not os.path.isdir(config_dir):
  os.makedirs(config_dir)

def save():
 """Dump configuration to disk."""
 create_config_dir()
 config.write()

create_config_dir()

import db

def make_dir_browser(dlg, label, value):
 """Create the control for the media directory selector."""
 ctrl = DirBrowseButton(dlg.panel, labelText = label)
 ctrl.SetValue(value)
 return ctrl

config = ConfigObj(os.path.join(config_dir, 'config.ini')) # The main configuration object.

# Create individual configuration sections:

# Sound Configuration.
config['sound'] = config.get('sound', {})
sound_config = config['sound']
sound_config.title = 'Sound'
spec = ConfigObj()
spec['fadeout_threshold'] = 'integer(min = 0, default = 0)'
spec['fadeout_amount'] = 'float(max = 1.0, min = -0.00001, default = 1.0)'
spec['volume_base'] = 'float(min = 1.00001, default = 10.0)'
sound_config.configspec = spec
sound_config.names = {
 'fadeout_threshold': 'Remaining Samples Before &Fadeout',
 'fadeout_amount': 'Fadeout &Amount',
 'volume_base': '&Volume Logarithm Base'
}
sound_config.controls = {
 'fadeout_amount': lambda dlg, name, value: FloatSpin(dlg.panel, value = value)
}

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

# Interface configuration.
config['interface'] = config.get('interface', {})
interface_config = config['interface']
interface_config.title = 'Interface'
spec = ConfigObj()
spec['clear_queue'] = 'boolean(default = True)'
spec['track_format'] = 'string(default = "{artist} - {album} - {number} - {title} ({duration})")'
spec['status_format'] = 'string(default = "{} ({} / {} loaded [{}%])")'
spec['results'] = 'integer(min = 1, max = 100, default = 25)'
interface_config.configspec = spec
interface_config.names = {
 'clear_queue': 'Clear The &Queue When Enter Is Pressed',
 'track_format': '&Track Format',
 'status_format': '&Status Bar Format',
 'results': '&Results To Download'
}

# Storage configuration.
config['storage'] = config.get('storage', {})
storage_config = config['storage']
storage_config.title = 'Storage'
spec = ConfigObj()
spec['media_dir'] = 'string(default = "%s")' % os.path.join(config_dir, 'media')
spec['quality'] = 'option("low", "med", "hi", default = "hi")'
spec['download'] = 'boolean(default = True)'
spec['lyrics'] = 'boolean(default = True)'
spec['max_size'] = 'integer(min = 5, default = 1024)'
storage_config.configspec = spec
storage_config.names = {
 'media_dir': '&Media Directory',
 'quality': 'Audio &Quality',
 'download': 'Download &tracks',
 'lyrics': 'Download &Lyrics',
}

storage_config.controls = {
 'media_dir': make_dir_browser,
 'quality': lambda dlg, name, value: StringChoice(dlg.panel, value, choices = ['hi', 'med', 'low'])
}

# Database configuration.
config['db'] = config.get('db', {})
db_config = config['db']
db_config.title = 'Database'
def db_config_updated():
 db.engine.echo = db_config['echo']
db_config.config_updated = db_config_updated
spec = ConfigObj()
spec['url'] = 'string(default = "sqlite:///%s")' % os.path.join(config_dir, 'catalogue.db') # The URL for the database.
spec['echo'] = 'boolean(default = False)' # The echo argument for create_engine.
db_config.configspec = spec
db_config.names = {
 'url': 'Database &URL (Only change if you know what you\'re doing)',
 'echo': 'Enable Database &Debugging',
}

config['system'] = config.get('system', {})
system_config = config['system']
spec = ConfigObj()
spec['stop_after'] = 'boolean(default = False)'
spec['shuffle'] = 'boolean(default = False)'
spec['volume'] = 'integer(min = 0, max = 100, default = 100)'
min_frequency = 100
max_frequency = 200000
spec['frequency'] = 'integer(min = {}, max = {}, default = 44100)'.format(min_frequency, max_frequency)
spec['pan'] = 'integer(min = 0, max = 100, default = 50)'
spec['offline_search'] = 'boolean(default = False)'
spec['repeat'] = 'option(0, 1, 2, default = 0)'
spec['output_device_index'] = 'integer(default = %s)' % application.output.device
spec['output_device_name'] = 'string(default = "%s")' % application.output.get_device_names()[application.output.device]
system_config.configspec = spec

def system_config_updated():
 """System config was updated."""
 application.frame.update_volume(system_config['volume'])

# All configuration sections must be created above this line.
# 
# Add all configuration sections to the below list in the order they should appear in the Options menu.
sections = [
 sound_config,
 login_config,
 interface_config,
 storage_config,
 db_config
]

validator = Validator()
for section in config.sections:
 config.validate(validator, section = config[section])

if system_config['output_device_name'] in application.output.get_device_names() and application.output.find_device_by_name(system_config['output_device_name']) == system_config['output_device_index'] and system_config['output_device_index'] != application.output.device:
 application.output.device = system_config['output_device_index']
