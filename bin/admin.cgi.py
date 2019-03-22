#!/usr/bin/env python3
# Encoding: UTF-8
#
# Lisence (BSD License 2.0)
#
# Copyright (c) 2018, 2019 Timo Seitz
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the <organization> nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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
  if rc: web.redirect(web.POST.get('next', ''), 3, 'MSG_USER_CREATED')
  else: log(0, 'ERR_USER_NOT_CREATED')

def handleForm():
  form = web.POST.get('_form', '')

  if form == 'newpass': web.changePassword()

  if web.SESSION.get('level', -1) < 100: return

  if form == 'addaccount': createUser()
  elif form in ('login', 'minilogin'): web.login()
  else: log(0, 'Unknown form: %s' % (form,))

web.handleForm = handleForm

def mainCGI():
  path = web.startCGI(init)
  hypertext.GLOBALS['session'] = web.SESSION

  level = web.SESSION.get('level', -1)
  if level <= 0:
    web.outputPage(hypertext.frame('<div class="form">\n' \
      + hypertext.form('login', target='login') + '\n</div>'))

  if len(path) == 0: path = ['users']

  if path[0] == 'profile':
    data = { 'session': web.SESSION, 'languages': sykeit.listLanguages() }
    web.outputPage(hypertext.frame('profile', data))

  if level < 200:
    log(0, lang['ERR_ACCESS_DENIED'])
  elif len(path) == 2 and path[0] == 'delete':
    if path[1] == web.SESSION['username']:
      web.redirect(os.environ.get('SCRIPT_NAME'), 5, 'ERR_DELETE_SELF')
    else:
      rc = database.removeUser(path[1])
      web.redirect(os.environ.get('SCRIPT_NAME'), 3,
        lang['MSG_USER_DELETED'] % (path[1],))
  elif path[0] == 'users':
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

  web.error404()

if __name__ == '__main__':
  if 'SERVER_ADDR' in os.environ: mainCGI()
  else: log(0, 'This must be run as CGI-script')

