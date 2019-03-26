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

import json, re, os
import hypertext, database, objects, web
CONFIG_FILES = [
  '~/.config/computer_manager.json',
  '/etc/cmanager/config.json',
  '/etc/computer_manager.json',
  os.sep.join(os.path.realpath(__file__).split(os.sep)[:-2]) \
    + '/computer_manager.json']
AVAILABLE_LANGUAGES = { 'en', 'fi' }
LANG = 'en'

lang = {}

REGEX_LANGFILE = re.compile(r'^lang-([a-z]{2}).json$')

def log(lvl, msg, *extra): print(msg)

if 'SERVER_ADDR' in os.environ:
  log = web.log
  database.log = log
  hypertext.log = log

def listLanguages():
  global AVAILABLE_LANGUAGES

  fdn = os.path.split(os.path.realpath(__file__))[0]
  AVAILABLE_LANGUAGES, lls = set(), []
  for fn in os.listdir(fdn):
    mt = REGEX_LANGFILE.match(fn)
    if mt is None: continue
    ln = mt.group(1)
    AVAILABLE_LANGUAGES.add(ln)
    with open(os.path.join(fdn, fn), 'r') as f:
      name = json.loads(f.read()).get('_LANG_NAME')
    lls.append({ 'id': ln, 'name': name })

  return lls

def init():
  global CONFIG_FILES, AVAILABLE_LANGUAGES, LANG, lang

  hypertext.GLOBALS['script'] = os.environ.get('SCRIPT_NAME', '')

  if 'CONFIG_FILE' in os.environ:
    CONFIG_FILES = [os.environ['CONFIG_FILE']] + CONFIG_FILES

  conf = {}
  for ffn in CONFIG_FILES:
    if os.path.exists(os.path.expanduser(ffn)):
      with open(ffn, 'r') as f: conf = json.loads(f.read())
      break
  if not conf: raise Exception('No config file')

  hypertext.JQUERY_UI_LOCATION = conf.get(
    'jquery_iu_location', hypertext.JQUERY_UI_LOCATION)
  hypertext.LAYOUT_DIRECTORY = conf.get('layout_directory')
  hypertext.FORMAT_DATE = conf.get('time_format', hypertext.FORMAT_DATE)
  web.SESSION_DIRECTORY = conf.get('session_directory', web.SESSION_DIRECTORY)

  hypertext.LAYOUT_DIRECTORY = os.path.expanduser(hypertext.LAYOUT_DIRECTORY)

  hypertext.GLOBALS['menu'] = [
    { 'title': '{{lang.COMPUTER_MANAGEMENT}}',
      'path': conf.get('path_computers',hypertext.PATH_COMPUTERS) },
    { 'title': '{{lang.ACCOUNT_MANAGEMENT}}',
      'path': conf.get('path_admin', hypertext.PATH_ADMIN) + '/users' },
    { 'title': '{{lang.PROFILE}}',
      'path': conf.get('path_admin', hypertext.PATH_ADMIN) + '/profile' } ]
  hypertext.GLOBALS['script'] = os.environ.get('SCRIPT_NAME', '')

  LANG = web.GET.get('lang') or web.COOKIES.get('lang') \
    or web.SESSION or conf.get('lang') or LANG

  if 'lang' in web.GET: web.COOKIES['lang'] = web.GET['lang']

  AVAILABLE_LANGUAGES = set()
  for fn in os.listdir(os.path.split(os.path.realpath(__file__))[0]):
    mt = REGEX_LANGFILE.search(fn)
    if mt is None: continue
    AVAILABLE_LANGUAGES.add(mt.group(1))

  if LANG not in AVAILABLE_LANGUAGES: log(0, 'Unknown language')
  if not os.path.isdir(hypertext.LAYOUT_DIRECTORY):
    log(0, 'Layout directory does not exist')

  hypertext.GLOBALS['scripts'].append('sort.js')

  web.STATIC_FILES.update({
    'sort.js':
      os.sep.join(os.path.realpath(__file__).split(os.sep)[:-1]+['sort.js']),
    'sort-none.svg':  hypertext.LAYOUT_DIRECTORY + os.sep + 'sort-none.svg',
    'sort-asc.svg':   hypertext.LAYOUT_DIRECTORY + os.sep + 'sort-asc.svg',
    'sort-desc.svg':  hypertext.LAYOUT_DIRECTORY + os.sep + 'sort-desc.svg',
    'move-up.svg':    hypertext.LAYOUT_DIRECTORY + os.sep + 'move-up.svg',
    'move-down.svg':  hypertext.LAYOUT_DIRECTORY + os.sep + 'move-down.svg',
    'info.svg':       hypertext.LAYOUT_DIRECTORY + os.sep + 'info.svg' })

  lang = hypertext.init(LANG)
  hypertext.lang = lang
  web.lang = lang

  database.configuration(conf)

  return conf

