#!/usr/bin/env python3
# Encoding: UTF-8
import random, string, json, time, sys, re, os
import database, objects, hypertext
CONFIG_FILES = ['~/.config/computer_manager.json',
  '/etc/computer_manager.json',
  os.path.split(os.path.realpath(__file__))[0] + '/computer_manager.json']

SESSION_DIRECTORY = '/tmp/session'
COOKIE_AGE = 14400
ENCODING, LANG, HTTP ='UTF-8', 'en', False
AVAILABLE_LANGUAGES = { 'en', 'fi' }
_SESSION, _COOKIES, _GET = None, {}, {}
_SHIFTS = {}

HTML_ERROR = '''<!DOCTYPE html><html>
  <head>
    <title>Error</title>
  </head><body>
    <p class="error">%s</p>
  </body>
</html>
'''
HTML_REDIRECT = '''<!DOCTYPE html><html>
  <head>
    <meta http-equiv="refresh" content="%d; URL=%s">
  </head><body>
%s
    <p>Redirecting to <a href="%s">%s</a></p>
  </body>
</html>
'''

lang = {}
_messages = []

LOG_BUFFER = 30
def log(lvl, message, extra=None):
  global LOG_BUFFER, _messages

  _messages.append((lvl, message, extra))
  if len(_messages) > LOG_BUFFER: _messages.pop(0)

  if lvl <= 1:
    sys.stderr.buffer.write(message.encode(ENCODING))
    if extra is not None:
      extra = '  %r\n' % (extra,)
      sys.stderr.buffer.write(extra.encode(ENCODING))

  if lvl == 0: outputPage(HTML_ERROR % (message,))

def init():
  global CONFIG_FILES, SESSION_DIRECTORY, LANG, _SHIFTS, _COOKIES, _GET, lang

  if 'CONFIG_FILE' in os.environ:
    CONFIG_FILES = [os.environ['CONFIG_FILE']] + CONFIG_FILES

  conf = {}
  for ffn in CONFIG_FILES:
    if os.path.exists(os.path.expanduser(ffn)):
      with open(ffn, 'r') as f: conf = json.loads(f.read())
      break
  if not conf: raise Exception('No config file')

  objects.SHIFT_NAMES = conf.get('shift_names', objects.SHIFT_NAMES)
  objects.DIRECTORY = conf.get('data_directory', objects.DIRECTORY)
  LANG = _GET.get('lang') or _COOKIES.get('lang') or conf.get('lang') or LANG
  hypertext.LAYOUT_DIRECTORY = conf.get('layout_directory', objects.DIRECTORY)
  SESSION_DIRECTORY = conf.get('session_directory', SESSION_DIRECTORY)

  database.configuration(conf)

  objects.SHIFTS = len(objects.SHIFT_NAMES)
  _SHIFTS = { objects.strip(nm): (i+1, nm)
    for i, nm in enumerate(objects.SHIFT_NAMES) }

  objects.DIRECTORY = os.path.expanduser(objects.DIRECTORY)
  hypertext.LAYOUT_DIRECTORY = os.path.expanduser(hypertext.LAYOUT_DIRECTORY)

  if LANG not in AVAILABLE_LANGUAGES: raise Exception('Unknown language')

  fdn = os.path.split(os.path.realpath(__file__))[0]
  ffn = os.path.join(fdn, 'lang-%s.json' % LANG)
  with open(ffn, 'r') as f: lang = json.loads(f.read())
  ffn = os.path.join(fdn, 'forms.json')
  with open(ffn, 'r') as f: hypertext.FORMS = json.loads(f.read())

  objects.lang = lang
  hypertext.lang = lang

  hypertext.GLOBALS['lang'] = lang
  hypertext.GLOBALS['script'] = os.environ.get('SCRIPT_NAME', '')

  hypertext.FUNCTIONS['menu'] = menu

  objects.loadData()

  hypertext.GLOBALS['list_days'] = enumerate(lang['WORKDAYS'])
  hypertext.GLOBALS['list_shifts'] \
    = [(i+1, d) for i, d in enumerate(objects.SHIFT_NAMES)]
  hypertext.GLOBALS['list_rooms'] \
    = [(i, r['name']) for i, r in enumerate(objects.ROOMS)]

  if 'lang' in _GET: _COOKIES['lang'] = _GET['lang']

def runCommand(cmd, *argv):
  argv = list(argv)
  if cmd == 'list':
    if not argv:
      cls = sorted(objects.Computer._COMPUTERS.values(), key=lambda c: c.cid)
      for cpu in cls:
        print('%s' % (cpu,))
        for usr in sorted(cpu.users, key=lambda u: u.shift):
          print('  %s' % (usr,))
    elif argv[0] in ('computers', 'computer', 'comp', 'cpu', 'c'):
      cls = sorted(objects.Computer._COMPUTERS.values(), key=lambda c: c.cid)
      for cpu in cls:
        print('%s' % (cpu,))
    elif argv[0] in ('users', 'user', 'usr', 'u'):
      for usr in sorted(objects.User._USERS.values(), key=lambda u: u.uid):
        print('%s' % (usr,))
    else:
      log(0, lang['ERR_UNKNOWN_LIST'] % argv[0])
  elif cmd == 'add':
    if not argv:
      print('You must give type')
      return
    tp = argv.pop(0)
    if   tp in ('computer', 'comp', 'cpu', 'c'):
      for cpu in argv:
        print('Adding computer %s' % cpu)
        objects.Computer(cpu)
    elif tp in ('user', 'usr', 'u'):
      for usr in argv:
        print('Adding user %s' % usr)
        objects.User(usr)
    else:
      print('Unknown type: %s' % tp)
    objects.saveData()
  elif cmd in ('delete', 'del', 'remove'):
    for nm in argv: objects.delete(nm)
    objects.saveData()
  elif cmd == 'shift':
    if len(argv) < 3:
      print('Not enough parameters')
      return
    addShift(argv[0], argv[1], argv[2:])

  elif cmd == 'seat':
    if len(argv) == 2: usr, cpu = argv
    elif len(argv) == 1: usr, cpu = argv[0], None

    usr = REGEX_STRIP.sub('', usr.lower())
    if usr in objects.User._USERS:
      usr = objects.User._USERS[usr]
      print('Adding seat %s for user %s' % (cpu, usr))
      usr.assignComputer(cpu)
      objects.saveData()
    else:
      print('Unknown user')
  else:
    print('Unknown command: %s' % cmd)

def main():
  init()

  if len(sys.argv) < 2: runCommand('list')
  else: runCommand(*sys.argv[1:])

def computersVacant(shift):
  ls = []
  for cpu in objects.Computer._COMPUTERS.values():
    sls = { usr.shift for usr in cpu.users }
    if shift not in sls: ls.append(cpu)
  return sorted(ls, key=lambda c: c.cid)

def handleForm():
  conf = {}
  if not os.environ.get('CONTENT_TYPE'): log(0, 'No form data')
  for key in os.environ['CONTENT_TYPE'].split(';'):
    key, val = key.strip(), 'true'
    if '=' in key: key, val = key.split('=', 1)
    key, val = key.strip(), val.strip()
    conf[key] = val
  if 'multipart/form-data' not in conf:
    log(0, 'Not a post form message', conf)
  data = sys.stdin.buffer.read()
  data = data.decode('UTF-8')
  formdata = {}
  for elm in data.split('--' + conf['boundary']):
    elm = elm.strip()
    if not elm or elm == '--': continue
    if not '\r\n\r\n' in elm: prop, val = elm, ''
    else: prop, val = elm.split("\r\n\r\n", 1)
    if not prop.startswith('Content-Disposition: form-data; '): continue
    prop = prop[32:]
    prop = dict([s.split('=', 1) for s in prop.split('; ')])
    if not 'name' in prop: continue
    key = prop['name'].strip('"')
    if key not in formdata: formdata[key] = val
    else:
      if isinstance(formdata[key], list): formdata[key].append(val)
      else: formdata[key] = [formdata[key], val]

  formData(formdata)

def formData(data):
  global _SESSION

  name = data.get('_form', '')
  if name == 'adduser':
    u = objects.User(data['name'], int(data['shift']),
      map(int, data.get('days', '')))
    if u in objects.User._USERS.values():
      log(2, lang['MSG_ADD_USER'] % (str(u),))
      objects.saveData()
    redirect('users', 3)
  elif name == 'updateuser':
    u = objects.User._USERS[data['uid']]
    rc = u.assignShift(int(data['shift']), map(int, data['days']))
    objects.saveData()
    redirect('user/%s' % data['uid'], 3)
  elif name == 'addcomputer':
    c = objects.Computer(data['name'])
    if c in objects.Computer._COMPUTERS.values():
      log(2, lang['MSG_ADD_COMPUTER'] % (str(c),))
      objects.saveData()
    redirect('computers', 3)
  elif name == 'login':
    _SESSION.update(database.checkPassword(data['username'], data['password']))
    if _SESSION.get('username'):
      writeSession()
      redirect(data.get('source') or data['_next'], 3)
    else: redirect('login/failed', 5)
  else: log(0, 'Unknown form: %s' % (name,))

  redirect(data.get('_next', ''), 3)

def printDebugData():
  html = ''
  for key in sorted(os.environ):
    html += "%s = %r<br>\n" % (key, os.environ[key])
  html += '<hr>\n'
  for t in _GET.items(): html += "%s = %r<br>\n" % t
  html += '<hr>\n'
  for t in _COOKIES.items(): html += "%s = %r<br>\n" % t
  outputPage(html)

def outputPage(html):
  global _COOKIES
  # Headers
  sys.stdout.write('Content-Type: text/html; charset=%s\r\n' % (ENCODING,))
  for c in _COOKIES.items():
    sys.stdout.write('Set-Cookie: %s=%s; Max-Age=%d;\r\n' % (c + (COOKIE_AGE,)))
  sys.stdout.write('\r\n')
  sys.stdout.flush()
  # HTML page
  sys.stdout.buffer.write(html.encode(ENCODING))
  # Write session and stop running
  writeSession()
  sys.exit(0)

def redirect(url, delay=None):
  if not (url.startswith('http://') or url.startswith('https://')):
    url = '%s/%s' % (os.environ.get('SCRIPT_NAME', ''), url)
  # Headers
  if delay is None:
    sys.stdout.write('Location: %s\r\n' % (url,))
  sys.stdout.write('Content-Type: text/html; charset=%s\r\n' % (ENCODING,))
  sys.stdout.write('\r\n')
  sys.stdout.flush()
  # HTML page
  messages = '<br>\n'.join([msg[1] for msg in _messages if msg[0] < 4])
  msg = HTML_REDIRECT % (delay, url, messages, url, url)
  sys.stdout.buffer.write(msg.encode(ENCODING))
  # Stop running
  sys.exit(0)

def menu():
  menu = { 'elements': [
    { 'title': '{{lang.COMPUTERS}}', 'path': 'computers' },
    { 'title': '{{lang.USERS}}', 'path': 'users' }]}
  for nm in objects.SHIFT_NAMES: menu['elements'].append({
    'title': nm, 'path': 'computers/' + nm })
  return hypertext.mustache('menu', menu)

def randomString(length=16):
  chars = string.ascii_letters + string.digits
  return ''.join([random.choice(chars) for i in range(length)])

def readSession(session_id):
  global SESSION_DIRECTORY, _SESSION

  if SESSION_DIRECTORY is None: return False
  if not os.path.isdir(SESSION_DIRECTORY):
    log(0, 'Session directory does not exist: %s' % SESSION_DIRECTORY)
    SESSION_DIRECTORY = None
    sys.exit(1)

  ffn = os.path.join(SESSION_DIRECTORY, '%s.json' % (session_id,))
  if not os.path.isfile(ffn): _SESSION = { 'id': session_id }
  else:
    st = os.stat(ffn)
    if st.st_mtime > time.time() + COOKIE_AGE: os.unlink(ffn)
    elif st.st_size > 0:
      with open(ffn, 'r') as f: _SESSION = json.loads(f.read())

  _SESSION['id'] = session_id

def writeSession(session_id=None):
  global SESSION_DIRECTORY, _SESSION

  if SESSION_DIRECTORY is None: return False
  if not os.path.isdir(SESSION_DIRECTORY):
    SESSION_DIRECTORY = None
    log(0, 'Session directory does not exist')
    sys.exit(1)

  if not session_id: session_id = _SESSION.get('id')
  if not session_id: return False

  ffn = os.path.join(SESSION_DIRECTORY, '%s.json' % (session_id,))
  with open(ffn, 'w') as f: _SESSION = f.write(json.dumps(_SESSION))

  return True

def destroySession(session_id=None):
  global SESSION_DIRECTORY, _SESSION, _COOKIES

  if SESSION_DIRECTORY is None or not os.path.isdir(SESSION_DIRECTORY): return

  if not session_id: session_id = _SESSION.get('id')
  if not session_id: return False

  # Destroy session file and generate new session id
  ffn = os.path.join(SESSION_DIRECTORY, '%s.json' % (session_id,))
  if os.path.isfile(ffn): os.unlink(ffn)
  _COOKIES['sessid'] = randomString(32)

  redirect('', 3)

def startCGI():
  global HTTP, _COOKIES, _SESSION, _GET

  HTTP = True

  _GET = dict([('=' in o and o.split('=', 1) or (o, True))
    for o in os.environ.get('QUERY_STRING', '').split('&') if o])

  _COOKIES = dict([o.strip().split('=')
    for o in os.environ.get('HTTP_COOKIE', '').split(';') if o])

  database.log = log
  objects.log = log
  hypertext.log = log
  init()

  if 'sessid' not in _COOKIES: _COOKIES['sessid'] = randomString(32)
  readSession(_COOKIES['sessid'])

  hypertext.GLOBALS['session'] = _SESSION

  path = os.environ.get('PATH_INFO', '/')
  path = [d for d in path.split('/') if d]

  if len(path) > 0:
    if   path[0] == 'login': handleForm()
    elif path[0] == 'logout': destroySession()

  return path

def mainCGI():
  global HTTP, _SHIFTS, _SESSION

  path = startCGI()
  if len(path) == 0: path = ['computers']
  usr_lvl = _SESSION.get('level', -1)

  if path[0] == 'debug' and usr_lvl >= 200: printDebugData()

  if usr_lvl >= 50:
    if path[0] == 'user' and len(path) == 2 and path[1] in objects.User._USERS:
      outputPage(hypertext.frame('user',
        { 'user': objects.User._USERS[path[1]].toDict() }))
    elif path[0] == 'computers':
      cls, shift = [], 0
      if len(path) > 1:
        sid = objects.strip(path[1])
        if sid in _SHIFTS: shift = _SHIFTS[sid][0]
      shfs = { i+1: { 'shift_name': n, 'presence': 5 * [True],
        'status': 'free', 'name': '{{lang.VACANT}}' }
          for i, n in enumerate(objects.SHIFT_NAMES) }
      for cpu in map(objects.Computer.toDict,
        objects.Computer._COMPUTERS.values()):
          uls = shfs.copy()
          for u in objects.User._USERS.values():
            if u.computer is None or u.computer.cid != cpu['cid']: continue
            uls[u.shift] = u.toDict()
          if shift > 0:
            cpu['user'] = uls.get(shift)
            cpu['users'] = []
          else:
            cpu['user'] =  uls.pop(1)
            cpu['users'] = [uls[i] for i in range(2, objects.SHIFTS+1)]
          cls.append(cpu)
      cls = sorted(cls, key=lambda c: c['name'])
      data = { 'shift_count': shift and 1 or objects.SHIFTS,
        'computers': cls }
      outputPage(hypertext.frame('computers', data))
    elif path[0] == 'users':
      uls = sorted(objects.User._USERS.values(), key=lambda u: u.name.lower())
      data = { 'users': [usr.toDict() for usr in uls] }
      outputPage(hypertext.frame('users', data))

  if usr_lvl >= 100:
    if path[0] == 'assign':
      if len(path) == 3 \
        and path[1] in objects.User._USERS \
        and path[2] in objects.Computer._COMPUTERS:
          objects.User._USERS[path[1]].assignComputer(path[2])
          objects.saveData()
          log(2, lang['MSG_ASSIGN_COMPUTER'] % (
            objects.Computer._COMPUTERS[path[2]].name,
            objects.User._USERS[path[1]].name))
          redirect('user/%s' % (path[1],), 3)
      elif len(path) == 2 and path[1] in objects.User._USERS:
        usr = objects.User._USERS[path[1]]
        dt = { 'user': usr.toDict(), 'computers':
          [{ 'id': cpu.cid, 'name': cpu.name }
            for cpu in computersVacant(usr.shift)] }
        outputPage(hypertext.frame(hypertext.mustache(
          hypertext.layout('assign'), dt)))
      else: log(0, lang['ERR_GERERIC']) #XXX
    elif path[0] == 'delete' and len(path) == 2:
      if path[1] in objects.User._USERS: rd = 'users'
      elif path[1] in objects.Computer._COMPUTERS: rd ='computers'
      else: rd = ''
      nm = objects.delete(path[1])
      if nm:
        objects.saveData()
        redirect(rd, 3, lang['MSG_DEL'] % (nm,))
      else:
        log(0, lang['ERR_UNKNOWN_UNIT'] % path[1])
    elif path[0] == 'form':
      handleForm()

  outputPage(hypertext.frame(hypertext.form('login', target='login')))

if __name__ == '__main__':
  if 'QUERY_STRING' in os.environ: mainCGI()
  else: main()

