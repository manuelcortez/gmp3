"""The main entry."""

if __name__ == '__main__':
 from default_argparse import parser
 args = parser.parse_args()
 import logging
 logging.basicConfig(stream = args.log_file, level = args.log_level)
 try:
  import application
  logging.info('Starting %s, version %s.', application.name, application.__version__)
  import db, config, os, os.path
  dir = config.config.storage['media_dir']
  application.library_size = sum([os.path.getsize(os.path.join(dir, x)) for x in os.listdir(dir) if os.path.isfile(os.path.join(dir, x))])
  logging.info('Library size is %s b (%.2f mb).', application.library_size, application.library_size / (1024 ** 2))
  logging.info('Working out of directory: %s.', config.config_dir)
  db.Base.metadata.create_all()
  from gui.main_frame import MainFrame
  application.frame = MainFrame(None)
  application.frame.Show(True)
  application.frame.Maximize()
  application.app.MainLoop()
  logging.info('Done.')
 except Exception as e:
  logging.exception(e)
