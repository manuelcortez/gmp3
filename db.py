"""Database specifics."""

import os.path
import application
import config
from datetime import timedelta
from attrs_sqlalchemy import attrs_sqlalchemy
from sqlalchemy import create_engine, Column, Table, ForeignKey, String
from sqlalchemy import Boolean, Integer, Interval, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, exc
from functions.util import format_timedelta

engine = create_engine(
    '%s.%d' % (
        config.config.db['url'], application.db_version
    ),
    echo=config.config.db['echo']
)
Base = declarative_base(bind=engine)
Session = sessionmaker(bind=engine)
session = Session()


def get_id(d):
    """Get the id from a dictionary d."""
    return d.get('storeId', d.get('nid', d.get('trackId', d.get('id'))))


artist_tracks = Table(
    'artist_tracks',
    Base.metadata,
    Column('artist_key', Integer(), ForeignKey('artists.key')),
    Column('track_key', Integer(), ForeignKey('tracks.key'))
)


playlist_tracks = Table(
    'playlist_tracks',
    Base.metadata,
    Column('playlist_key', Integer(), ForeignKey('playlists.key')),
    Column('track_key', Integer(), ForeignKey('tracks.key'))
)


@attrs_sqlalchemy
class Artist(Base):
    """The artists table."""
    __tablename__ = 'artists'
    key = Column(Integer(), primary_key=True)
    id = Column(String(30), nullable=False)
    name = Column(String(200), nullable=True)
    bio = Column(String(10000), nullable=True)
    tracks = relationship('Track', secondary=artist_tracks)

    def populate(self, d):
        """Load data from a dictionary d."""
        self.name = d.get('name', 'Unknown Artist')
        self.bio = d.get('artistBio')

    def __str__(self):
        return '<Unloaded>' if self.name is None else self.name


@attrs_sqlalchemy
class Track(Base):
    """An object representing a track."""
    __tablename__ = 'tracks'
    key = Column(Integer(), primary_key=True)
    album = Column(String(200), nullable=False)
    album_art_url = Column(String(500), nullable=True, default=None)
    album_artist = Column(String(200), nullable=False)
    album_id = Column(String(30), nullable=False)
    artist = Column(String(200), nullable=False)
    artists = relationship('Artist', secondary=artist_tracks)
    composer = Column(String(200), nullable=False)
    deleted = Column(Boolean(), nullable=False)
    disc_number = Column(Integer(), nullable=False)
    duration = Column(Interval())
    filename = Column(String(500), nullable=True)
    genre = Column(String(100), nullable=False)
    id = Column(String(30), nullable=True)
    kind = Column(String(10), nullable=False)
    last_played = Column(DateTime(), nullable=True)
    lyrics = Column(String(100000), nullable=True)
    play_count = Column(Integer(), nullable=False)
    playlists = relationship('Playlist', secondary=playlist_tracks)
    store_id = Column(String(30), nullable=False)
    title = Column(String(200), nullable=False)
    track_number = Column(Integer(), nullable=False)
    track_type = Column(String(5), nullable=False)
    year = Column(Integer(), nullable=False)

    @property
    def in_library(self):
        """Return True if this track is in the google library."""
        return not self.id.startswith('T')

    @property
    def length(self):
        """Return the duration in the proper format."""
        return format_timedelta(self.duration)

    @property
    def path(self):
        """Return an appropriate path for this result."""
        return os.path.join(
            config.config.storage['media_dir'],
            self.id + '.mp3'
        )

    @property
    def downloaded(self):
        """Return whether or not this track is downloaded."""
        return os.path.isfile(self.path)

    @property
    def number(self):
        """Return the track number, padded with 0's."""
        return '%s%s' % (
            '0' if self.track_number is not None and self.track_number < 10
               else '',
            self.track_number
        )

    def populate(self, d):
        """Populate from a dictionary d."""
        self.album = d.get('album', 'Unknown Album')
        try:
            self.album_art_url = d['albumArtRef'][0]['url']
        except IndexError:
            pass  # There is no album art.
        self.album_artist = d.get('albumArtist', 'Unknown Album Artist')
        self.album_id = d['albumId']
        self.artist = d.get('artist', 'Unknown Artist')
        for id in d.get('artistId', []):
            try:
                artist = session.query(Artist).filter(Artist.id == id).one()
            except exc.NoResultFound:
                artist = Artist(id=id)
            self.artists.append(artist)
        self.composer = d.get('composer', 'Unknown Composer')
        self.deleted = d.get('deleted', False)
        self.disc_number = d.get('discNumber', 1)
        self.duration = timedelta(
            seconds=int(d.get('durationMillis', '0')) / 1000
        )
        self.genre = d.get('genre', 'No Genre')
        self.id = d.get('id', self.id)
        if self.id is None:
            self.id = get_id(d)
        self.kind = d['kind']
        self.play_count = d.get('playCount', 0)
        self.store_id = d.get('storeId', self.id)
        self.title = d.get('title', 'Untitled Track')
        self.track_number = d.get('trackNumber', 1)
        self.track_type = d['trackType']
        self.year = d.get('year', 1)

    def __str__(self):
        return '{0.artist} - {0.title}'.format(self)


def to_object(item):
    """Return item as a Track object."""
    try:
        track = session.query(
            Track
        ).filter(
            Track.store_id == get_id(
                item
            )
        ).one()
    except exc.NoResultFound:
        track = Track()
        track.populate(item)
        session.add(track)
    return track


def list_to_objects(l):
    """Return a list of database objects seeded from a list l."""
    for item in l:
        yield to_object(item)


config.config.interface.result_format.title = \
   'Track &Format (Possible Formatters: %s)' % ', '.join(
    [
        x for x in dir(Track) if not x.startswith('_')
    ])


@attrs_sqlalchemy
class Playlist(Base):
    __tablename__ = 'playlists'
    key = Column(Integer(), primary_key=True)
    id = Column(String(30), nullable=False)
    name = Column(String(500), nullable=False)
    description = Column(String(10000), nullable=False)
    tracks = relationship('Track', secondary=playlist_tracks)


@attrs_sqlalchemy
class PlaylistEntry(Base):
    __tablename__ = 'playlist_entries'
    key = Column(Integer(), primary_key=True)
    id = Column(String(30), nullable=False)
    playlist_id = Column(Integer(), ForeignKey('playlists.key'))
    playlist = relationship('Playlist', backref='entries')
    track_id = Column(Integer(), ForeignKey('tracks.key'))
    track = relationship('Track', backref='playlist_entries')


@attrs_sqlalchemy
class Station(Base):
    __tablename__ = 'stations'
    key = Column(Integer(), primary_key=True)
    id = Column(String(30), nullable=False)
    name = Column(String(500), nullable=False)


@attrs_sqlalchemy
class URLStream(Base):
    """A URL stream, like an internet radio station."""
    __tablename__ = 'urls'
    key = Column(Integer(), primary_key=True)
    name = Column(String(50), nullable=False)
    url = Column(String(500), nullable=False)

    def __str__(self):
        return self.name
