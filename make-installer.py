"""Generate the installer script."""

import application
from jinja2 import Environment, FileSystemLoader

environment = Environment(loader = FileSystemLoader('.'))

if __name__ == '__main__':
 with open('installer.iss', 'w') as f:
  f.write(
   environment.get_template('installer.iss.template').render(
    app_name = application.name,
    app_version = application.__version__
   )
  )
 import os
 os.system('start installer.iss &')
