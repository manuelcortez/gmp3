"""The Klein instance."""

import os.path, application, wx, config, logging
from klein import Klein
from twisted.python import log
from twisted.web.server import Site
from twisted.internet import reactor
from jinja2 import Environment, loaders
from json import dumps
from db import Track
from .forms import SearchForm
from functions.util import format_track as _format_track
from functools import wraps

logger = logging.getLogger(__name__)

environment = Environment(loader = loaders.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))
environment.globals['app_name'] = application.name
environment.globals['app_version'] = application.__version__
environment.globals['app_url'] = application.url

def jsonify(data):
 """Utility function to return json."""
 return dumps(data)

def format_track(track):
 """Format a track."""
 if isinstance(track, Track):
  return _format_track(track)
 else:
  return 'Not a track'

environment.filters['format_track'] = format_track

def render_template(name, *args, **kwargs):
 """Render the template named name with args and kwargs."""
 template = environment.get_template(name)
 return template.render(*args, **kwargs)

class App(Klein):
 """An app which doesn't let any unauthorized people in."""
 def run(self, host, port, log_file):
  """Start running the server on host:port."""
  log.startLogging(log_file)
  reactor.listenTCP(port, Site(self.resource()), interface=host)
  reactor.run(False)
 def route(self, *args, **kwargs):
  logger.info('app.route(%r, %r).', args, kwargs)
  decorator = super(App, self).route(*args, **kwargs)
  def f(func):
   """Also decorates func."""
   logger.debug('Decorating %r.', func)
   @wraps(func)
   def login_check(request, *args, **kwargs):
    """Check we're logged in."""
    if config.config.http['enabled']:
     username, password = (request.getUser(), request.getPassword())
     if hasattr(username, 'decode'):
      username = username.decode()
     if hasattr(password, 'decode'):
      password = password.decode()
     logger.debug('Checking credentials (%r, %r)...', username, password)
     if username == config.config.http['uid'] and password == config.config.http['pwd']:
      logger.debug('Returning function %r.', func)
      return func(request, *args, **kwargs)
     else:
      logger.debug('Login failed.')
      request.setResponseCode(401)
      request.setHeader(b'WWW-Authenticate', b'Basic')
      return 'You must login to view this resource.'
    else:
     logger.warning('Attempted conection while the HTTP server is disabled.')
     request.loseConnection()
   return decorator(login_check)
  return f

app = App()

class NotFound(Exception):
 pass # Let the template handle it.

@app.handle_errors(NotFound)
def not_found(request, failure):
 """404."""
 request.setResponseCode(404)
 return render_template('not_found.html', request = request)

class DataHolder(object):
 """A way of getting around the multithreaded nature of GMP."""
 def __init__(self, data = None):
  """Initialise and set self.data."""
  self.data = data
  self.finished = False
 
 def load(self, func, wait = True):
  """Run function then set self.finished = True. If wait is True then wait for completion."""
  wx.CallAfter(self._load, func)
  if wait:
   while not self.finished:
    pass
  return self.data
 
 def _load(self, func):
  """Actually do the dirty work."""
  self.data = func(self)
  self.finished = True

def load_data(func):
 """Using the main thread, load data with func and return it."""
 holder = DataHolder()
 return holder.load(func)

@app.route('/')
def home(request):
 """The main page."""
 return render_template('index.html', form = SearchForm())

from . import tracks

__all__ = [
 'environment',
 'render_template',
 'app',
 'NotFound',
 'DataHolder',
 'load_data',
 'home',
 'tracks',
]
