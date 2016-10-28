"""The main entry for the jukebox."""

if __name__ == '__main__':
    from default_argparse import parser
    from db import Base, session, Playlist
    Base.metadata.create_all()
    from config import config
    parser.add_argument('--host', default = '0.0.0.0', help = 'The interface on which to run the web server')
    parser.add_argument('-p', '--port', type = int, default = 5853, help = 'The port to run the Jukebox on')
    parser.add_argument('-d', '--default-playlist', help = 'The playlist to play tracks from when nothing else is playing')
    parser.add_argument('-i', '--interval', type = float, default = 0.2, help = 'How often should the jukebox check the queue')
    
    parser.add_argument('username', nargs = '?', default = config.login['uid'], help = 'Your google username')
    parser.add_argument('password', nargs = '?', default = config.login['pwd'], help = 'Your Google password')
    args = parser.parse_args()
    if not args.username:
        args.username = input('Enter your Google username: ')
    if not args.password:
        from getpass import getpass
        args.password = getpass('Password: ')
    import logging
    logging.basicConfig(stream = args.log_file, level = args.log_level, format = args.log_format)
    from jukebox.api import api
    if api.login(args.username, args.password, api.FROM_MAC_ADDRESS):
        from jukebox.app import app, play_manager
        if not args.default_playlist:
            from jukebox.cmenu import Menu
            menu = Menu('Choose a default playlist')
            for playlist in session.query(Playlist).all():
                menu.add_entry(playlist.name, lambda p = playlist: setattr(app, 'default', p))
            set_default = menu.get_selection()
            if callable(set_default):
                set_default()
            else:
                app.default = None
        else:
            query = session.query(Playlist).filter(Playlist.name == args.default_playlist)
            if query.count():
                app.default = query.first()
            else:
                logging.critical('No playlists found matching %s.', args.default_playlist)
                raise SystemExit
        if app.default is None:
            logging.warning('Nothing will be played when there are no items in the queue.')
        else:
            logging.info('When no tracks are queued, random tracks from the %s playlist will be played.', app.default.name)
        from jukebox import pages
        logging.info('Loaded pages from %r.', pages)
        from twisted.internet.task import LoopingCall
        loop = LoopingCall(play_manager)
        args.interval = abs(args.interval)
        logging.info('Checking the queue every %.2f seconds.', args.interval)
        loop.start(args.interval)
        app.run(args.host, args.port, logFile = args.log_file)
    else:
        logging.critical('Login failed.')
