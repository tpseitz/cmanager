# Encoding: UTF-8
import json, re, os
import hypertext, database, web
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

  hypertext.LAYOUT_DIRECTORY = conf.get('layout_directory')
  web.SESSION_DIRECTORY = conf.get('session_directory', web.SESSION_DIRECTORY)

  hypertext.LAYOUT_DIRECTORY = os.path.expanduser(hypertext.LAYOUT_DIRECTORY)

  hypertext.GLOBALS['menu'] = [
    { 'title': '{{lang.COMPUTER_MANAGEMENT}}',
      'path': conf.get('path_computers',hypertext.PATH_COMPUTERS) },
    { 'title': '{{lang.ACCOUNT_MANAGEMENT}}',
      'path': conf.get('path_admin', hypertext.PATH_ADMIN) + '/users' },
    { 'title': '{{lang.PROFILE}}',
      'path': conf.get('path_admin', hypertext.PATH_ADMIN) } ]
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

  lang = hypertext.loadLanguage(LANG)
  hypertext.lang = lang
  web.lang = lang

  database.configuration(conf)

  return conf

