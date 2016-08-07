"""Database specifics."""

import os.path
from config import db_config, storage_config, interface_config
from sqlalchemy import create_engine, Column, Table, ForeignKey, String, Boolean, Integer, Interval, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, exc
from datetime import timedelta

engine = create_engine(db_config['url'], echo = db_config['echo'])
Base = declarative_base(bind = engine)
Session = sessionmaker(bind = engine)
session = Session()

def get_id(d):
 """Get the id from a dictionary d."""
 return d.get('storeId', d.get('id', d.get('trackId', d.get('nid'))))

artist_tracks = Table('artist_tracks',
 Base.metadata,
 Column('artist_key', Integer(), ForeignKey('artists.key')),
 Column('track_key', Integer(), ForeignKey('tracks.key'))
)

playlist_tracks = Table('playlist_tracks',
 Base.metadata,
 Column('playlist_key', Integer(), ForeignKey('playlists.key')),
 Column('track_key', Integer(), ForeignKey('tracks.key'))
)

class Artist(Base):
 __tablename__ = 'artists'
 key = Column(Integer(), primary_key = True)
 id = Column(String(length = 30), nullable = False)
 name = Column(String(length = 200), nullable = True)
 bio = Column(String(length = 10000), nullable = True)
 tracks = relationship('Track', secondary = artist_tracks)
 
 def populate(self, d):
  """Load data from a dictionary d."""
  self.name = d.get('name', 'Unknown Artist')
  self.bio = d.get('artistBio')
 
 def __str__(self):
  return '<Unloaded>' if self.name is None else self.name

class Track(Base):
 __tablename__ = 'tracks'
 key = Column(Integer(), primary_key = True)
 album = Column(String(length = 200), nullable = False)
 album_art_url = Column(String(length = 500), nullable = True, default = None)
 album_artist = Column(String(length = 200), nullable = False)
 album_id = Column(String(length = 30), nullable = False)
 artist = Column(String(length = 200), nullable = False)
 artists = relationship('Artist', secondary = artist_tracks)
 composer = Column(String(length = 200), nullable = False)
 deleted = Column(Boolean(), nullable = False)
 disc_number = Column(Integer(), nullable = False)
 duration = Column(Interval())
 filename = Column(String(length = 500), nullable = True, default = None)
 genre = Column(String(length = 100), nullable = False)
 id = Column(String(length = 30), nullable = True)
 last_played = Column(DateTime(), nullable = True, default = None)
 lyrics = Column(String(length = 100000), nullable = True)
 play_count = Column(Integer(), nullable = False)
 playlists = relationship('Playlist', secondary = playlist_tracks)
 store_id = Column(String(length = 30), nullable = False)
 title = Column(String(length = 200), nullable = False)
 track_number = Column(Integer(), nullable = False)
 year = Column(Integer(), nullable = False)
 
 @property
 def path(self):
  """Return an appropriate path for this result."""
  return os.path.join(storage_config['media_dir'], self.id + '.mp3')
 
 @property
 def downloaded(self):
  """Return whether or not this track is downloaded."""
  return os.path.isfile(self.path)
 
 @property
 def number(self):
  """Return the track number, padded with 0's."""
  return '%s%s' % ('0' if self.track_number is not None and self.track_number < 10 else '', self.track_number)
 def populate(self, d):
  """Populate from a dictionary d."""
  self.album = d.get('album', 'Unknown Album')
  try:
   self.album_art_url = d['albumArtRef'][0]['url']
  except IndexError:
   pass # There is no album art.
  self.album_artist = d.get('albumArtist', 'Unknown Album Artist')
  self.album_id = d['albumId']
  self.artist = d.get('artist', 'Unknown Artist')
  for id in d.get('artistId', []):
   try:
    artist = session.query(Artist).filter(Artist.id == id).one()
   except exc.NoResultFound:
    artist = Artist(id = id)
   self.artists.append(artist)
  self.composer = d.get('composer', 'Unknown Composer')
  self.deleted = d.get('deleted', False)
  self.disc_number = d.get('discNumber', 1)
  self.duration = timedelta(seconds = int(d.get('durationMillis', '0')) / 1000)
  self.genre = d.get('genre', 'No Genre')
  self.id = d.get('id', get_id(d))
  self.play_count = d.get('playCount', 0)
  self.store_id = d.get('storeId', self.id)
  self.title = d.get('title', 'Untitled Track')
  self.track_number = d.get('trackNumber', 1)
  self.year = d.get('year', 1)
 
 def __str__(self):
  return '{0.artist} - {0.title}'.format(self)

def to_object(item):
 """Return item as a Track object."""
 try:
  track = session.query(Track).filter(Track.id == item.get('id', get_id(item))).one()
 except exc.NoResultFound:
  track = Track()
  track.populate(item)
 session.add(track)
 return track

def list_to_objects(l):
 """Return a list of database objects seeded from a list l."""
 for item in l:
  yield to_object(item)

interface_config.names['track_format'] = 'Track &Format (Possible Formatters: %s)' % ', '.join([x for x in dir(Track) if not x.startswith('_')])

class Playlist(Base):
 __tablename__ = 'playlists'
 key = Column(Integer(), primary_key = True)
 id = Column(String(length = 30), nullable = False)
 name = Column(String(length = 500), nullable = False)
 description = Column(String(length = 10000), nullable = False)
 tracks = relationship('Track', secondary = playlist_tracks)

class PlaylistEntry(Base):
 __tablename__ = 'playlist_entries'
 key = Column(Integer(), primary_key = True)
 id = Column(String(length = 30), nullable = False)
 playlist_id = Column(Integer(), ForeignKey('playlists.key'))
 playlist = relationship('Playlist', backref = 'entries')
 track_id = Column(Integer(), ForeignKey('tracks.key'))
 track = relationship('Track', backref = 'playlist_entries')

class Station(Base):
 __tablename__ = 'stations'
 key = Column(Integer(), primary_key = True)
 id = Column(String(length = 30), nullable = False)
 name = Column(String(length = 500), nullable = False)
