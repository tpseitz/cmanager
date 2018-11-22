#!/usr/bin/env python3
# Encoding: UTF-8
import datetime, json, os
import hypertext, database, web

CONFIG_FILES = ['~/.config/computer_manager.json',
  '/etc/computer_manager.json',
  os.path.split(os.path.realpath(__file__))[0] + '/computer_manager.json']
USER_LEVELS = { 0: 'User', 50: 'Observer', 100: 'Master', 200: 'Admin' }

lang = {}
log = web.log
database.log = log
hypertext.log = log

def init():
  global CONFIG_FILES, USER_LEVELS, LANG, _SHIFTS, lang

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
  if 'user_levels' in conf:
    USER_LEVELS = { int(k): v for k, v in conf['user_levels'].items() }

  hypertext.GLOBALS['menu'] = [
    { 'title': '{{lang.COMPUTER_MANAGEMENT}}',
      'path': conf.get('path_computers',hypertext.PATH_COMPUTERS) },
    { 'title': '{{lang.ACCOUNT_MANAGEMENT}}',
      'path': conf.get('path_admin', hypertext.PATH_ADMIN) } ]

  hypertext.GLOBALS['submenu'] = False

  lang = hypertext.loadLanguage(conf.get('lang', 'en'))
  hypertext.GLOBALS['script'] = os.environ.get('SCRIPT_NAME', '')

  hypertext.GLOBALS['list_roles'] = [
    (i, USER_LEVELS[i]) for i in sorted(USER_LEVELS)]
  hypertext.FUNCTIONS['menu'] = {}

  database.configuration(conf)

def createUser():
  if web.SESSION.get('level', -1) < 200:
    log(0, lang['ERR_ACCESS_DENIED'])
    return

  username = web.POST.get('username')
  fullname = web.POST.get('fullname')
  password = web.POST.get('password1')
  passchk  = web.POST.get('password2')
  level    = web.POST.get('level', 0)

  if not username:
    log(0, lang['ERR_NO_FULLNAME'])
    return
  if not username:
    log(0, lang['ERR_NO_USERNAME'])
    return
  if password != passchk:
    log(0, lang['ERR_PASSWORD_MISMATCH'])
    return

  rc = database.createUser(username, fullname, level, password)
  if rc: web.redirect(web.POST.get('next', ''), 1, lang['MSG_USER_CREATED'])
  else: log(0, 'Could not create user')

def handleForm():
  if web.SESSION.get('level', -1) < 100: return

  form = web.POST.get('_form', '')
  if form == 'addaccount': createUser()
  elif form in ('login', 'minilogin'): web.login()
  else: log(0, 'Unknown form: %s' % (form,))

web.handleForm = handleForm

def mainCGI():
  path = web.startCGI(init)
  hypertext.GLOBALS['session'] = web.SESSION

  level = web.SESSION.get('level', -1)
  if level <= 0:
    web.outputPage(hypertext.frame('<div class="form">' \
      + hypertext.form('login', target='login') + '</div>'))
  elif level < 200:
    log(0, lang['ERR_ACCESS_DENIED'])
    return
  elif len(path) == 2 and path[0] == 'delete':
    if path[1] == web.SESSION['username']:
      web.redirect(os.environ.get('SCRIPT_NAME'), 1, lang['ERR_DELETE_SELF'])
    else:
      rc = database.removeUser(path[1])
      web.redirect(os.environ.get('SCRIPT_NAME'), 1,
        lang['MSG_USER_DELETED'] % (path[1],))
  else:
    accounts = database.listAccounts()
    for acc in accounts:
      for lvl in sorted(USER_LEVELS):
        if acc['level'] >= lvl: acc['level_name'] = USER_LEVELS[lvl]
      if acc.get('lastlogin'):
        acc['lastlogin_name'] = datetime.datetime.fromtimestamp(
          acc['lastlogin']).strftime('%Y-%m-%d %H:%M:%S')
      else: acc['lastlogin_name'] = '{{lang.NEVER}}'
    data = { 'accounts': accounts }
    web.outputPage(hypertext.frame('accounts', data))

  web.outputPage('You shouldn\'t see this')

if __name__ == '__main__':
  if 'QUERY_STRING' in os.environ: mainCGI()
  else: web.outputPage('NO!')

