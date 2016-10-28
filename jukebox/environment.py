"""The jinja2 environment."""

import application, os.path
from datetime import timedelta
from jinja2 import Environment, FileSystemLoader
from functions.util import format_track, format_timedelta
from .settings import ISettings
from .app import app

environment = Environment(
    loader = FileSystemLoader(os.path.join('jukebox', 'templates'))
)

environment.filters['format_track'] = format_track
environment.filters['format_timedelta'] = format_timedelta
environment.globals['app_name'] = '{0.name} V{0.__version__}'.format(application)
environment.globals['app'] = app

def render_template(request, name, *args, **kwargs):
    """
    Render a template and return it as a string.
    
    Return the resulting template rendered with args and kwargs.
    
    The following keyword arguments are provided by this function unless overridden:
    session - The session object for the request.
    settings - The ISettings for session.
    duration - A timedelta representing the duration of the queue.
    """
    template = environment.get_template(name)
    kwargs.setdefault('request', request)
    kwargs.setdefault('session', request.getSession())
    settings = ISettings(kwargs['session'])
    kwargs.setdefault('settings', settings)
    kwargs.setdefault('duration', sum([track.duration for track in app.queue], timedelta()))
    return template.render(*args, **kwargs)
