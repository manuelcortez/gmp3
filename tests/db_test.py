"""Test the database."""

import config
config.db_url = 'sqlite:///gmp-test.sqlite3'

from tests import api
from db import *

Base.metadata.create_all()

track = Track()

def test_track():
 d = api.search('test')['song_hits'][0]['track']
 track.populate(d)
 session.add(track)

def test_artist():
 assert session.query(Track).count()
 a = session.query(Artist).first()
 assert a is not None
 d = api.get_artist_info(a.id)
 a.populate(d)
 assert a.name is not None
 assert a.bio is not None
