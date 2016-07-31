import sys, configobj
sys.path.insert(0, '.')

config = configobj.ConfigObj('creds.ini')

if not config.get('uid'):
 print('No credentials found in creds.ini file found. Creating test configuration.')
 config['uid'] = input('Username: ')

if not config.get('pwd'):
 from getpass import getpass
 config['pwd'] = getpass('Password: ')

from gmusicapi import Mobileclient

api = Mobileclient()

config.write()
if not api.login(config['uid'], config['pwd'], api.FROM_MAC_ADDRESS):
 config['uid'] = ''
 config['pwd'] = ''
 quit('Login failed.')

from config import db_config
db_config['url'] = 'sqlite:///test.db'
