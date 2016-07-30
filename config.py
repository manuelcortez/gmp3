"""Configuration stuff."""

import application, os, os.path
from configobj import ConfigObj
from validate import Validator

config_dir = application.paths.GetUserDataDir()

def save():
 """Dump configuration to disk."""
 if not os.path.isdir(config_dir):
  os.makedirs(config_dir)
 config.write()

config = ConfigObj(os.path.join(config_dir, 'config.ini')) # The main configuration object.

# Create individual configuration sections:

# Database configuration.
config['db'] = {}
db_config = config['db']
spec = ConfigObj()
spec['url'] = 'string(default = "sqlite:///catalogue.db")' # The URL for the database.
spec['echo'] = 'boolean(default = False)' # The echo argument for create_engine.
db_config.configspec = spec
db_config.names = {
 'url': 'Database &URL (Only change if you know what you\'re doing)',
 'echo': 'Enable Database &Debugging'
}

validator = Validator()
for section in config.sections:
 config.validate(validator, section = config[section])
