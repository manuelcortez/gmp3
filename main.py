"""The main entry."""

if __name__ == '__main__':
 import db
 db.Base.metadata.create_all()
 from gui.main_frame import MainFrame
 import application
 application.frame = MainFrame(None)
 application.frame.Show(True)
 application.frame.Maximize()
 application.app.MainLoop()
