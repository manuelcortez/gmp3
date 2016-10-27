"""
settings.py: Session-specific settings.
"""

from zope.interface import Interface, Attribute, implementer
from twisted.python.components import registerAdapter
from twisted.web.server import Session

class ISettings(Interface):
    """Settings for the current session."""
    tracks = Attribute('The tracks loaded for this session.')

@implementer(ISettings)
class Settings(object):
    def __init__(self, session):
        self.tracks = []

registerAdapter(Settings, Session, ISettings)
