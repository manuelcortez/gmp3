"""Configuration stuff."""

import application, os, os.path, wx, logging
from wx.lib.filebrowsebutton import DirBrowseButton
from simpleconf import Section, Option
from simpleconf.validators import Integer, Boolean, Float, Option as OptionValidator
from gui.widgets import StringChoice

logger = logging.getLogger(__name__)

config_dir = application.paths.GetUserLocalDataDir()

def create_config_dir():
 """Create the configuration directory."""
 if not os.path.isdir(config_dir):
  os.makedirs(config_dir)

def save():
 """Dump configuration to disk."""
 create_config_dir()
 config.write(indent = 1)

create_config_dir()

import db

min_frequency = 100
max_frequency = 200000

class EchoOption(Option):
 def set(self, value):
  """Update the db engine as well."""
  super(EchoOption, self).set(value)
  if hasattr(db, 'engine'): # Just in case db isn't properly initialised yet.
   db.engine.echo = value

class Config(Section):
 """The main configuration object."""
 filename = os.path.join(config_dir, 'config.json')
 class sound(Section):
  """Sound Configuration."""
  title = 'Sound'
  fadeout_threshold = Option(0, title = 'Remaining Samples Before &Fadeout', validator = Integer(min = 0))
  fadeout_amount = Option(1.0, title = 'Fadeout &Amount', validator = Float(max = 1.0, min = 0.00001))
  volume_base = Option(10.0, title = '&Volume Logarithm Base', validator = Float(min = 1.00001, max = 100.0))
  option_order = [fadeout_threshold, fadeout_amount, volume_base]
 
 class login(Section):
  """Login configuration."""
  title = 'Login'
  uid = Option('', title = '&Username')
  pwd = Option('', title = '&Password', control = lambda option, window: wx.TextCtrl(window.panel, style = wx.TE_PASSWORD))
  remember = Option(True, title = '&Remember Credentials', validator = Boolean)
  option_order = [uid, pwd, remember]
 
 class interface(Section):
  """Interface configuration."""
  title = 'Interface'
  clear_queue = Option(True, title = 'Clear The &Queue When Enter Is Pressed', validator = Boolean)
  track_format = Option('{artist} - {album} - {number} - {title} ({duration})', title = '&Track Format')
  status_bar_format = Option('{text} ({loaded} / {total} loaded {percentage}%) [{duration}]', title = '&Status Bar Format')
  results = Option(25, title = '&Results To Download', validator = Integer(min = 1, max = 100))
  option_order = [clear_queue, track_format, status_bar_format, results]
 
 class storage(Section):
  """Storage configuration."""
  title = 'Storage'
  media_dir = Option(os.path.join(config_dir, 'media'), title = '&Media Directory', control = lambda option, window: DirBrowseButton(window.panel, labelText = option.get_title()))
  quality = Option('hi', title = 'Audio &Quality', control = lambda option, window: StringChoice(window.panel, option.value, choices = option.validator.options), validator = OptionValidator('hi', 'med', 'low'))
  download = Option(True, title = 'Download &tracks', validator = Boolean)
  lyrics = Option(True, title = 'Download &Lyrics', validator = Boolean)
  max_size = Option(1024, title = '&Maximum size of the media directory In Megabytes', validator = Integer(min = 5))
  option_order = [media_dir, quality, download, lyrics, max_size]
 
 class db(Section):
  """Database configuration."""
  title = 'Database'
  url = Option('sqlite:///%s' % os.path.join(config_dir, 'catalogue.db'), title = 'Database &URL (Only change if you know what you\'re doing)')
  echo = EchoOption(False, title = 'Enable Database &Debugging', validator = Boolean)
  option_order = [url, echo]
 
 class system(Section):
  """System configuration."""
  title = 'System'
  visible = False # We do our own filtering anyway, but just to be on the safe side.
  stop_after = Option(False, validator = Boolean)
  shuffle = Option(False, validator = Boolean)
  volume = Option(100, validator = Integer(min = 0, max = 100))
  frequency = Option(44100, validator = Integer(min = min_frequency, max = max_frequency))
  pan = Option(50, validator = Integer(min = 0, max = 100))
  offline_search = Option(False, validator = Boolean)
  repeat = Option(0, validator = Integer(min = 0, max = 2))
  output_device_index = Option(application.output.device, validator = Integer(min = -1))
  output_device_name = Option(application.output.get_device_names()[application.output.device])
 
 def load(self):
  """Load configuration from disk."""
  try:
   super(Config, self).load()
   logger.info('Loaded the configuration from %s.', self.filename)
  except Exception as e:
   logger.warning('Failed to load the configuration from %s, error follows.', self.filename)
   logger.exception(e)

config = Config()

# The below list should contain all configuration sections in the order they should appear in the menu.

sections = [
 config.sound,
 config.login,
 config.interface,
 config.storage,
 config.db
]

if config.system['output_device_name'] in application.output.get_device_names() and application.output.find_device_by_name(config.system['output_device_name']) == config.system['output_device_index'] and config.system['output_device_index'] != application.output.device:
 application.output.device = config.system['output_device_index']
