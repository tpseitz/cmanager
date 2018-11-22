# Encoding: UTF-8
import random, string, json, time, sys, os
import database

SESSION_DIRECTORY = '/tmp/session'
COOKIE_AGE, COOKIE_PATH = 14400, '/'
ENCODING ='UTF-8'
LOG_BUFFER = 30
SESSION, COOKIES, POST, GET = {}, {}, {}, {}

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

_messages = []

def handleForm(): log(0, 'No subroutine')

def log(lvl, message, extra=None):
  global LOG_BUFFER, _messages

  _messages.append((lvl, message, extra))
  if len(_messages) > LOG_BUFFER: _messages.pop(0)

  if lvl <= 1:
    sys.stderr.buffer.write(message.encode(ENCODING))
    if extra is not None:
      extra = '  %r\n' % (extra,)
      sys.stderr.buffer.write(extra.encode(ENCODING))
    sys.stdout.flush()

  if lvl == 0:
    sys.stdout.buffer.write(b'Content-Type: text/html; charset=UTF-8\r\n\r\n'
      + (HTML_ERROR % (message,)).encode('UTF-8'))
    sys.exit(0)

def outputPage(html):
  global COOKIES
  # Headers
  sys.stdout.write('Content-Type: text/html; charset=%s\r\n' % (ENCODING,))
  for key, val in COOKIES.items():
    if val == 'PHPSESSID': continue
    sys.stdout.write('Set-Cookie: %s=%s; Path=%s; Max-Age=%d;\r\n' \
      % (key, val, COOKIE_PATH, COOKIE_AGE))
  sys.stdout.write('\r\n')
  sys.stdout.flush()
  # HTML page
  sys.stdout.buffer.write(html.encode(ENCODING))
  # Write session and stop running
  writeSession()
  sys.exit(0)

def redirect(url, delay=None, *msg):
  if delay is None:
    sys.stdout.write('Location: %s\r\n' % (url,))

  if not (url.startswith('http://') or url.startswith('https://')
    or url.startswith('/')):
      url = '%s/%s' % (os.environ.get('SCRIPT_NAME', ''), url)

  messages = '<br>\n'.join([msg[1] for msg in _messages if msg[0] < 4])
  outputPage(HTML_REDIRECT % (delay or 0, url, messages, url, url))

def randomString(length=16):
  chars = string.ascii_letters + string.digits
  return ''.join([random.choice(chars) for i in range(length)])

def readSession(session_id):
  global SESSION_DIRECTORY, SESSION
  SESSION = {}

  if SESSION_DIRECTORY is None: return False
  if not os.path.isdir(SESSION_DIRECTORY):
    log(0, 'Session directory does not exist: %s' % SESSION_DIRECTORY)
    SESSION_DIRECTORY = None
    sys.exit(1)

  ffn = os.path.join(SESSION_DIRECTORY, '%s.json' % (session_id,))
  if not os.path.isfile(ffn): SESSION = { 'id': session_id }
  else:
    st = os.stat(ffn)
    if st.st_mtime > time.time() + COOKIE_AGE: os.unlink(ffn)
    elif st.st_size > 0:
      with open(ffn, 'r') as f: SESSION = json.loads(f.read())

  SESSION['id'] = session_id

def writeSession(session_id=None):
  global SESSION_DIRECTORY, SESSION

  if SESSION_DIRECTORY is None: return False
  if not os.path.isdir(SESSION_DIRECTORY):
    SESSION_DIRECTORY = None
    log(0, 'Session directory does not exist')
    sys.exit(1)

  if not session_id: session_id = SESSION.get('id')
  if not session_id: return False

  ffn = os.path.join(SESSION_DIRECTORY, '%s.json' % (session_id,))
  with open(ffn, 'w') as f: SESSION = f.write(json.dumps(SESSION))

  return True

def destroySession(session_id=None):
  global SESSION_DIRECTORY, SESSION, COOKIES

  if SESSION_DIRECTORY is None or not os.path.isdir(SESSION_DIRECTORY): return

  if not session_id: session_id = SESSION.get('id')
  if not session_id: return False

  # Destroy session file and generate new session id
  ffn = os.path.join(SESSION_DIRECTORY, '%s.json' % (session_id,))
  if os.path.isfile(ffn): os.unlink(ffn)
  COOKIES['sessid'] = randomString(32)

  redirect(os.environ.get('HTTP_REFERER', '/'), 3)

def login():
  global SESSION, POST

  if not POST: log(0, 'No post data')

  SESSION.update(database.checkPassword(
    POST.get('username', ''), POST.get('password', '')))
  if SESSION.get('username'):
    writeSession()
    redirect(POST.get('source') or POST['_next'], 3)
  else: redirect('login/failed', 5)

def handlePOST():
  global POST

  if 'CONTENT_TYPE' not in os.environ: return
#  log(0, 'Post: %r' % os.environ.get('CONTENT_TYPE')) #XXX

  conf = {}
  for key in os.environ['CONTENT_TYPE'].split(';'):
    key, val = key.strip(), 'true'
    if '=' in key: key, val = map(str.strip, key.split('=', 1))
#    key, val = key.strip(), val.strip()
    conf[key] = val
  if 'multipart/form-data' not in conf:
    log(0, 'Not a post form message', conf)
  data = sys.stdin.buffer.read()
  data = data.decode('UTF-8')
  POST = {}
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
    if key not in POST: POST[key] = val
    else:
      if isinstance(POST[key], list): POST[key].append(val)
      else: POST[key] = [POST[key], val]

def startCGI(init=None):
  global HTTP, COOKIES, SESSION, GET

  HTTP = True

  GET = dict([('=' in o and o.split('=', 1) or (o, True))
    for o in os.environ.get('QUERY_STRING', '').split('&') if o])

  COOKIES = dict([o.strip().split('=')
    for o in os.environ.get('HTTP_COOKIE', '').split(';') if o])

  handlePOST()

  if init is not None: init()

  if 'sessid' not in COOKIES: COOKIES['sessid'] = randomString(32)
  readSession(COOKIES['sessid'])

  path = os.environ.get('PATH_INFO', '/')
  path = [d for d in path.split('/') if d]

  if len(path) > 0:
    form = POST.get('_form')
    if   path[0] == 'login': login()
    elif form in ('login','minilogin'): login()
    elif path[0] == 'logout': destroySession()
    elif path[0] == 'form': handleForm()

  return path

