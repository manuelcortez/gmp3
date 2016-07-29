"""Database specifics."""

import config
from sqlalchemy import create_engine, Column, Table, ForeignKey, String, Boolean, Integer, Interval, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, exc
from datetime import datetime, timedelta

engine = create_engine(config.db_config['url'], echo = config.db_config['echo'])
Base = declarative_base(bind = engine)
Session = sessionmaker(bind = engine)
session = Session()

artist_tracks = Table('artist_tracks',
 Base.metadata,
 Column('artist_key', Integer(), ForeignKey('artists.key')),
 Column('track_key', Integer(), ForeignKey('tracks.key'))
)

class Artist(Base):
 __tablename__ = 'artists'
 key = Column(Integer(), primary_key = True)
 id = Column(String(length = 30), nullable = False)
 name = Column(String(length = 200), nullable = True)
 bio = Column(String(length = 10000), nullable = True)
 tracks = relationship('Track', secondary = artist_tracks)
 
 def __str__(self):
  return self.name

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
 genre = Column(String(length = 100), nullable = False)
 id = Column(String(length = 30), nullable = False)
 last_played = Column(DateTime(), nullable = False)
 lyrics = Column(String(length = 100000), nullable = True)
 play_count = Column(Integer(), nullable = False)
 title = Column(String(length = 200), nullable = False)
 track_number = Column(Integer(), nullable = False)
 year = Column(Integer(), nullable = False)
 
 def populate(self, d):
  """Populate from a dictionary d."""
  self.album = d.get('album', 'Unknown Album')
  ref = d.get('albumArtRef', [])
  if ref:
   self.album_art_url = ref[0]['url']
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
  self.id = d.get('storeId', d.get('id', d.get('trackId', d.get('nid'))))
  self.last_played = datetime.now()
  self.play_count = d.get('playCount', 0)
  self.title = d.get('title', 'Untitled Track')
  self.track_number = d.get('trackNumber', 1)
  self.year = d.get('year', 1)
 
 def __str__(self):
  return '{0.artist} - {0.title}'.format(self)
