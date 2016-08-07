"""The main entry."""

if __name__ == '__main__':
 from default_argparse import parser
 args = parser.parse_args()
 import logging
 logging.basicConfig(stream = args.log_file, level = args.log_level)
 try:
  import application
  logging.info('Starting %s, version %s.', application.name, application.__version__)
  import db
  db.Base.metadata.create_all()
  from gui.main_frame import MainFrame
  application.frame = MainFrame(None)
  application.frame.Show(True)
  application.frame.Maximize()
  application.app.MainLoop()
  logging.info('Done.')
 except Exception as e:
  logging.exception(e)
