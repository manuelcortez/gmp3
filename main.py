"""The main entry."""

if __name__ == '__main__':
    from default_argparse import parser
    parser.add_argument(
        '--server-host',
        default='0.0.0.0',
        help='The host to run the HTTP server on'
    )
    parser.add_argument(
        '--server_port',
        default=4673,
        type=int,
        help='The port to run the HTTP server on'
    )
    args = parser.parse_args()
    import logging
    logging.basicConfig(stream=args.log_file, level=args.log_level)
    try:
        import application
        logging.info(
            'Starting %s, version %s.',
            application.name,
            application.__version__
        )
        import os
        import os.path
        import db
        import config
        from humanize import naturalsize
        dir = config.config.storage['media_dir']
        if os.path.isdir(dir):
            application.library_size = sum(
                [
                    os.path.getsize(
                        os.path.join(
                            dir,
                            x
                        )
                    ) for x in os.listdir(
                        dir
                    ) if os.path.isfile(
                        os.path.join(
                            dir,
                            x
                        )
                    )
                ]
            )
        else:
            application.library_size = 0
        logging.info(
            'Library size is %s.',
            naturalsize(application.library_size)
        )
        logging.info('Working out of directory: %s.', config.config_dir)
        db.Base.metadata.create_all()
        from gui.main_frame import MainFrame
        application.frame = MainFrame(None)
        application.frame.Show(True)
        application.frame.Maximize(True)
        from threading import Thread
        from server.base import app
        app.port = args.server_port
        from twisted.web.server import Site
        from twisted.internet import reactor, endpoints
        endpoint_description = "tcp:port={0}:interface={1}".format(
            args.server_port,
            args.server_host
        )
        endpoint = endpoints.serverFromString(reactor, endpoint_description)
        endpoint.listen(Site(app.resource())).addCallback(
            lambda result: logging.info(
                'Web server running on port %d.',
                result.port
            )
        )
        Thread(target=reactor.run, args=[False]).start()
        application.app.MainLoop()
        reactor.callFromThread(reactor.stop)
        logging.info('Done.')
    except Exception as e:
        logging.exception(e)
