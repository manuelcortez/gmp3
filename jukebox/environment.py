"""The jinja2 environment."""

import application, os.path
from jinja2 import Environment, FileSystemLoader
from functions.util import format_track
from .settings import ISettings
from .app import app

environment = Environment(
    loader = FileSystemLoader(os.path.join('jukebox', 'templates'))
)

environment.filters['format_track'] = format_track
environment.globals['app_name'] = '{0.name} V{0.__version__}'.format(application)

def render_template(request, name, *args, **kwargs):
    """
    Render a template and return it as a string.
    
    Return the resulting template rendered with args and kwargs.
    
    The following keyword arguments are provided by this function unless overridden:
    session - The session object for the request.
    settings - The ISettings for session.
    """
    template = environment.get_template(name)
    kwargs.setdefault('request', request)
    kwargs.setdefault('session', request.getSession())
    settings = ISettings(kwargs['session'])
    if not settings.tracks and app.default is not None:
        settings.tracks = app.default.tracks
    kwargs.setdefault('settings', settings)
    return template.render(*args, **kwargs)
