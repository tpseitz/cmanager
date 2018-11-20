#!/usr/bin/env python3
# Encoding: UTF-8
import json, os
import hypertext, database, web

CONFIG_FILES = ['~/.config/computer_manager.json',
  '/etc/computer_manager.json',
  os.path.split(os.path.realpath(__file__))[0] + '/computer_manager.json']

log = hypertext.log
lang = {}

def init():
  global CONFIG_FILES, LANG, _SHIFTS, lang

  if 'CONFIG_FILE' in os.environ:
    CONFIG_FILES = [os.environ['CONFIG_FILE']] + CONFIG_FILES

  conf = {}
  for ffn in CONFIG_FILES:
    if os.path.exists(os.path.expanduser(ffn)):
      with open(ffn, 'r') as f: conf = json.loads(f.read())
      break
  if not conf: raise Exception('No config file')

  hypertext.LAYOUT_DIRECTORY = conf.get('layout_directory')
  web.SESSION_DIRECTORY = conf.get('session_directory', web.SESSION_DIRECTORY)

  lang = hypertext.loadLanguage(conf.get('lang', 'en'))
  hypertext.GLOBALS['script'] = os.environ.get('SCRIPT_NAME', '')

  hypertext.FUNCTIONS['menu'] = {}

  database.configuration(conf)

def createUser():
  if web.SESSION.get('level', -1) < 200:
    log(0, lang['ERR_ACCESS_DENIED'])
    return

  username = web.POST.get("username")
  password = web.POST.get("password")
  level = web.POST.get("role", 0)

def mainCGI():
  path = web.startCGI(init)
  hypertext.GLOBALS['session'] = web.SESSION

  level = web.SESSION.get('level', -1)
  if level <= 0:
    web.outputPage(hypertext.frame(hypertext.form('login', target='login')))
  elif level < 200:
    log(0, lang['ERR_ACCESS_DENIED'])
    return

if __name__ == '__main__':
  if 'QUERY_STRING' in os.environ: mainCGI()

