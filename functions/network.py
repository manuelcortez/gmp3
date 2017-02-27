"""Internet-related functions."""

from urllib.request import Request, urlopen
import application, wx, os, os.path
from requests import get
from lyricscraper import lyrics
from .util import prune_library

def download_track(url, path):
 """Download URL to path."""
 response = get(url)
 folder = os.path.dirname(path)
 if not os.path.isdir(folder):
  os.makedirs(folder)
 with open(path, 'wb') as f:
  application.library_size += f.write(response.content)
 wx.CallAfter(prune_library) # Delete old tracks if necessry.

def get_lyrics(track):
 """Get the lyrics of the provided track."""
 return lyrics.get_lyrics(track.artist, track.title)

def get_stream_title(stream_url):
 """Code modified from:
 http://stackoverflow.com/questions/6613587/reading-shoutcast-icecast-metadata-from-a-radio-stream-with-python"""
 request = Request(stream_url)
 request.add_header('Icy-MetaData', 1)
 response = urlopen(request)
 icy_metaint_header = response.headers.get('icy-metaint')
 if icy_metaint_header is not None:
  metaint = int(icy_metaint_header)
  read_buffer = metaint+256
  content = response.read(read_buffer)
  title = content[metaint:].split("'".encode())[1].decode()
  return title
