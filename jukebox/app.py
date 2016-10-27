"""The Klein instance."""

import os, os.path, logging
from random import choice
from klein import Klein
from requests import get
from .api import api

logger = logging.getLogger(__name__)

app = Klein()
app.track = None # The currently-playing track.
app.queue = [] # The tracks to be played.

from sound_lib.stream import FileStream

def download_track(url, path):
    """Download URL to path."""
    response = get(url)
    folder = os.path.dirname(path)
    if not os.path.isdir(folder):
        os.makedirs(folder)
    with open(path, 'wb') as f:
        f.write(response.content)

def play_manager():
    """Play the next track."""
    if app.track is None or not app.track.is_playing: # The current track has finished playing
        if app.queue:
            track = app.queue.pop(0)
        else:
            if app.default is not None:
                track = choice(app.default.tracks)
            else:
                return # Nothing to be done.
        if track.artists[0].bio is None:
            track.artists[0].populate(api.get_artist_info(track.artists[0].id))
        if not track.downloaded:
            url = api.get_stream_url(track.id)
            download_track(url, track.path)
        logger.info('Playing track: %s.', track)
        app.track = FileStream(file = track.path)
        app.track.play()
            
