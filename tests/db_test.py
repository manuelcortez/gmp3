"""Test the database."""

import config
config.db_url = 'sqlite:///gmp-test.sqlite3'

import db
from tests import api

from unittest import TestCase

class TestDB(TestCase):
 session = db.session
 db.Base.metadata.create_all()
 track = db.Track()
 
 def test_track(self):
  d = api.search('test')['song_hits'][0]['track']
  self.track.populate(d)
  self.session.add(self.track)
  assert self.session.commit() is None
