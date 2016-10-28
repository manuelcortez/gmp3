"""Jukebox app routes."""

from sqlalchemy.orm.exc import NoResultFound
from db import session, Track, Base, list_to_objects
from .app import app
from .api import api
from .environment import render_template
from .search_form import SearchForm
from .util import convert
from .settings import ISettings
from multidict import MultiDict

Base.metadata.create_all()

@app.route('/')
def home(request):
    """Home page."""
    form = SearchForm()
    if request.args:
        data = convert(request.args)
        if 'search' in data:
            data['search'] = data['search'][0]
        form.process(
            MultiDict(
                data
            )
        )
        search = form.data.get('search')
        if search:
            results = api.search(search)
            results = [result['track'] for result in results.get('song_hits', [])]
            ISettings(request.getSession()).tracks = list_to_objects(results)
    return render_template(request, 'index.html', form = form)

@app.route('/queue_track/<id>')
def queue_track(request, id):
    """Queue the requested track."""
    try:
        track = session.query(Track).filter(Track.id == id).one()
        queued = track in app.queue
        if not queued:
            app.queue.append(track)
    except NoResultFound:
        track = None
        queued = False
    return render_template(
        request,
        'track_queued.html',
        track = track,
        queued = queued
    )
