#!/usr/bin/env python3
# Encoding: UTF-8
import datetime, os
import hypertext, database, sykeit, web

USER_LEVELS = { 0: 'User', 50: 'Observer', 100: 'Master', 200: 'Admin' }

lang = {}
log = web.log

def init():
  global CONFIG_FILES, USER_LEVELS, lang

  conf = sykeit.init()
  lang = sykeit.lang

  if 'user_levels' in conf:
    USER_LEVELS = { int(k): v for k, v in conf['user_levels'].items() }

  hypertext.GLOBALS['list_roles'] = [
    (i, USER_LEVELS[i]) for i in sorted(USER_LEVELS)]

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
  else: log(0, 'ERR_USER_NOT_CREATED')

def changePassword():
  if web.SESSION.get('level', -1) <= 0:
    log(0, lang['ERR_NOT_LOGGED_IN'])
    return

  username = web.SESSION.get('username')
  oldpass  = web.POST.get('oldpass')
  newpass  = web.POST.get('newpass')
  passchk  = web.POST.get('passchk')

  if password != passchk:
    log(0, 'ERR_PASSWORD_MISMATCH')
    return

  rc = database.updatePassword(username, newpass, oldpass)
  if rc: web.redirect(web.POST.get('next', ''), 1, lang['MSG_USER_CREATED'])
  else: log(0, 'ERR_PASSWORD_CHANGE')

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
  if 'SERVER_ADDR' in os.environ: mainCGI()
  else: log(0, 'This must be run as CGI-script')

