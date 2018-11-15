#!/usr/bin/env python3
# Encoding: UTF-8
import random, string, json, sys, re, os
import database, objects, hypertext
CONFIG_FILE = '/etc/computer_manager.json'
ENCODING, LANG, HTTP ='UTF-8', 'en', False
AVAILABLE_LANGUAGES = { 'en', 'fi' }
_SESSION, _COOKIES, _GET = None, {}, {}
_SHIFTS = {}

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

def log(lvl, message, extra=None):
  _messages.append((lvl, message, extra))
  if lvl <= 1: sys.stderr.buffer.write(message.encode(ENCODING))
  if extra is not None:
    extra = '  %r\n' % (extra,)
    sys.stderr.buffer.write(extra.encode(ENCODING))
  if lvl == 0: outputPage(message + "\n")

def init():
  global CONFIG_FILE, LANG, _SHIFTS, _COOKIES, _GET, lang

  conf = {}
  CONFIG_FILE = os.path.expanduser(CONFIG_FILE)
  if not os.path.isfile(CONFIG_FILE): raise Exception('No config file')
  if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r') as f: conf = json.loads(f.read())

  objects.SHIFT_NAMES = conf.get('shift_names', objects.SHIFT_NAMES)
  objects.DIRECTORY = conf.get('data_directory', objects.DIRECTORY)
  LANG = _GET.get('lang') or _COOKIES.get('lang') or conf.get('lang') or LANG
  hypertext.LAYOUT_DIRECTORY = conf.get('layout_directory', objects.DIRECTORY)

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
    prop, val = elm.split("\r\n\r\n", 1)
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
    _SESSION = database.checkPassword(data['username'], data['password'])
    if _SESSION: redirect(data.get('source') or data['_next'], 3)
    else: redirect('login/failed')
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
  for c in _COOKIES.items(): sys.stdout.write('Set-Cookie: %s=%s\r\n' % c)
  sys.stdout.write('\r\n')
  sys.stdout.flush()
  # HTML page
  sys.stdout.buffer.write(html.encode(ENCODING))
  # Stop running
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

def mainCGI():
  global HTTP, _SHIFTS, _COOKIES, _SESSION, _GET

  HTTP = True

  _GET = dict([('=' in o and o.split('=', 1) or (o, True))
    for o in os.environ.get('QUERY_STRING', '').split('&') if o])

  _COOKIES = dict([o.strip().split('=')
    for o in os.environ.get('HTTP_COOKIE', '').split(';') if o])
  if 'sessid' not in _COOKIES: _COOKIES['sessid'] = randomString(32)

  _SESSION = {}

  init()
  database.log = log
  objects.log = log
  hypertext.log = log

  path = os.environ.get('PATH_INFO', '/')
  path = [d for d in path.split('/') if d]
  if not _SESSION: outputPage(hypertext.frame(hypertext.form('login')))
  elif len(path) == 0: redirect('computers')
#  elif : printDebugData()
  elif path[0] == 'user' and len(path) == 2 and path[1] in objects.User._USERS:
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
  elif path[0] == 'assign':
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
      redirect(rd, 3)
#      outputPage(lang['MSG_DEL'] % (nm,))
    else:
      log(0, lang['ERR_UNKNOWN_UNIT'] % path[1])
  elif path[0] == 'form':
    handleForm()

  outputPage(hypertext.frame('No data'))

if __name__ == '__main__':
  if 'QUERY_STRING' in os.environ: mainCGI()
  else: main()

