"""Configuration stuff."""

import application, os.path
from configobj import ConfigObj
from validate import Validator

config_dir = application.paths.GetUserDataDir()

config = ConfigObj(os.path.join(config_dir, 'config.ini')) # The main configuration object.

# Create individual configuration sections:

# Database configuration.
config['db'] = {}
db_config = config['db']
spec = ConfigObj()
spec['url'] = 'string(default = "sqlite:///db.sqlite3")'
spec['echo'] = 'boolean(default = False)'
db_config.configspec = spec
db_config.names = {
 'url': 'Database &URL (Only change if you know what you\'re doing)',
 'echo': 'Enable Database &Debugging'
}

validator = Validator()
for section in config.sections:
 config.validate(validator, section = config[section])
