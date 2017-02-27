"""Utility functions."""

import logging
import os
import os.path
import wx
import application
import db
from humanize import naturalsize
from gui.login_frame import LoginFrame
from config import config
from sqlalchemy.orm.exc import NoResultFound
from gmusicapi.exceptions import NotLoggedIn, AlreadyLoggedIn
from functools import partial

logger = logging.getLogger(__name__)


def do_login(callback=lambda *args, **kwargs: None, args=[], kwargs={}):
    """Try to log in, then call callback."""
    def f(callback, *args, **kwargs):
        # Free it up so more login attempts can be made if needed.
        application.logging_in = False
        return callback(*args, **kwargs)
    cb = partial(f, callback, *args, **kwargs)
    if application.logging_in:
        return  # Don't try again.
    application.logging_in = True
    try:
        if not config.login[
            'uid'
        ] or not config.login[
            'pwd'
        ] or not application.api.login(
            config.login[
                'uid'
            ],
            config.login[
                'pwd'
            ],
            application.api.FROM_MAC_ADDRESS
        ):
            return LoginFrame(cb).Show(True)
    except AlreadyLoggedIn:
        pass
    return cb()


def load_playlist(playlist):
    """Load a playlist into the database."""
    try:
        p = db.session.query(
            db.Playlist
        ).filter(
            db.Playlist.id == playlist[
                'id'
            ]
        ).one()
    except NoResultFound:
        p = db.Playlist()
        p.id = playlist['id']
    db.session.add(p)
    p.name = playlist.get('name', 'Untitled Playlist')
    p.description = playlist.get('description', '')
    p.tracks = []
    for t in playlist.get('tracks', []):
        if 'track' in t:
            track = db.to_object(t['track'])
            p.tracks.append(track)
            i = t['id']
            try:
                e = db.session.query(
                    db.PlaylistEntry
                ).filter(
                    db.PlaylistEntry.id == i,
                    db.PlaylistEntry.track == track,
                    db.PlaylistEntry.playlist == p
                ).one()
            except NoResultFound:
                e = db.PlaylistEntry(
                    playlist=p,
                    track=track,
                    id=t['id']
                )
            db.session.add(e)
    db.session.commit()
    application.frame.add_playlist(p)
    return p


def do_error(message, title='Error'):
    """Display an error message."""
    wx.CallAfter(wx.MessageBox, str(message), title, style=wx.ICON_EXCLAMATION)


def delete_playlist(playlist):
    """Delete a playlist."""
    try:
        if application.api.delete_playlist(playlist.id) == playlist.id:
            from server import tracks
            if playlist in tracks.storage.playlists:
                tracks.storage.playlists.remove(playlist)
            for e in playlist.entries:
                db.session.delete(e)
            db.session.delete(playlist)
            if playlist in application.frame.playlists:
                application.frame.playlists_menu.Delete(
                    application.frame.playlists[playlist]
                )
                del application.frame.playlists[playlist]
            db.session.commit()
            return True
        else:
            return False
    except NotLoggedIn:
        do_login(callback=delete_playlist, args=[playlist])
        return True


def format_track(track):
    """Return track printed as the user likes."""
    if isinstance(track, db.URLStream):
        return '{0.name} ({0.url})'.format(track)
    else:
        return config.interface[
            'result_format'
        ].format(
            **{
                x: getattr(
                    track,
                    x
                ) for x in dir(
                    track
                ) if not x.startswith(
                    '_'
                )
            }
        )


def load_station(station):
    """Return a Station object from a dictionary."""
    try:
        s = db.session.query(
            db.Station
        ).filter(
            db.Station.id == station['id']
        ).one()
    except NoResultFound:
        s = db.Station(id=station['id'])
    db.session.add(s)
    s.name = station.get('name', 'Untitled Radio Station')
    application.frame.add_station(s)
    return s


def clean_library():
    """Remove unwanted files and directories from the media directory."""
    dir = config.storage['media_dir']
    if os.path.isdir(dir):
        tracks = ['%s.mp3' % t.id for t in db.session.query(db.Track).all()]
        for thing in os.listdir(dir):
            path = os.path.join(dir, thing)
            if os.path.isdir(path):
                logger.info('Removing directory %s.', path)
                os.removedirs(path)
            else:
                if thing not in tracks:
                    logger.info('Removing file %s.', path)
                    os.remove(path)


def prune_library():
    """Delete the least recently downloaded tracks in the catalogue."""
    goal = application.library_size - config.storage['max_size'] * (1024 ** 2)
    if goal > 0:
        logger.info(
            'Pruning %s of data...',
            naturalsize(
                goal
            )
        )
        for r in db.session.query(
            db.Track
        ).filter(
            db.Track.last_played.isnot(
                None
            )
        ).order_by(
                db.Track.last_played.asc()
        ).all():
            if r.downloaded:
                size = os.path.getsize(r.path)
                logger.info(
                    'Deleting %s (%s).',
                    r,
                    naturalsize(size)
                )
                goal -= size
                application.library_size -= size
                os.remove(r.path)
                if goal <= 0:
                    logger.info('Done.')
                    break
        else:
            logger.warning(
                'Failed with %s left.',
                naturalsize(goal)
            )
    else:
        logger.info(
            'No need for prune. %s left.',
            naturalsize(goal * -1)
        )


def format_timedelta(td):
    """Format timedelta td."""
    fmt = []  # The format as a list.
    seconds = int(td.total_seconds())
    years, seconds = divmod(seconds, 31536000)
    if years:
        fmt.append('%d %s' % (years, 'year' if years == 1 else 'years'))
    months, seconds = divmod(seconds, 2592000)
    if months:
        fmt.append('%d %s' % (months, 'month' if months == 1 else 'months'))
    days, seconds = divmod(seconds, 86400)
    if days:
        fmt.append('%d %s' % (days, 'day' if days == 1 else 'days'))
    hours, seconds = divmod(seconds, 3600)
    if hours:
        fmt.append('%d %s' % (hours, 'hour' if hours == 1 else 'hours'))
    minutes, seconds = divmod(seconds, 60)
    if minutes:
        fmt.append(
            '%d %s' % (minutes, 'minute' if minutes == 1 else 'minutes')
        )
    if seconds:
        fmt.append(
            '%d %s' % (seconds, 'second' if seconds == 1 else 'seconds')
        )
    if len(fmt) == 1:
        return fmt[0]
    else:
        res = ''
        for pos, item in enumerate(fmt):
            if pos == len(fmt) - 1:
                res += ', and '
            elif res:
                res += ', '
            res += item
        return res
