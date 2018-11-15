# Encoding: UTF-8
import crypt, hmac, time, re
import MySQLdb
HOSTNAME, USERNAME, PASSWORD, DATABASE = 'localhost', None, None, None
MAX_TRIES = 5

REGEX_USERNAME = re.compile(r'^[a-z][a-z\d]+$')
REGEX_ESCAPE = re.compile(r'["\';\\]')

def log(lvl, message, *extra):
  print(message)
  for e in extra: print('  %s' % (e,))

def configuration(conf):
  global HOSTNAME, USERNAME, PASSWORD, DATABASE

  HOSTNAME = conf.get('db_hostname', HOSTNAME)
  USERNAME = conf.get('db_username', USERNAME)
  PASSWORD = conf.pop('db_password', PASSWORD)
  DATABASE = conf.get('db_database', DATABASE)

__CONNECTION = None
def _cursor():
  global __CONNECTION
  if not __CONNECTION:
    __CONNECTION = MySQLdb.connect(HOSTNAME, USERNAME, PASSWORD, DATABASE)
  return __CONNECTION.cursor()

def close():
  global __CONNECTION
  if __CONNECTION:
    __CONNECTION.commit()
    __CONNECTION.close()
  __CONNECTION = None

def checkPassword(username, password):
  username = username.lower()
  if not REGEX_USERNAME.match(username):
    log(1, 'Illegal username: %s' % (username,))
    return None

  cur = _cursor()
  query = 'SELECT id, password, tries, username, fullname, lastlogin' \
    + ' FROM users WHERE username = %s'
  cur.execute(query, (username,))
  rows = cur.fetchall()

  if len(rows) != 1:
    if len(rows) > 1: log(0, 'Database error: More than one result')
    else: log(2, 'Wrong username or password') #TODO
    return None
  uid, pwhash, tries, username, fullname, lastlogin = rows[0]
  print(pwhash) #XXX

  if tries > MAX_TRIES:
    log(2, 'This account is locked')
    return None

  hsh = crypt.crypt(password, pwhash)
  print(hsh) #XXX
  if hmac.compare_digest(hsh, pwhash):
    query = 'UPDATE users SET lastlogin = %s, tries = %s WHERE id = %s'
    cur.execute(query, (int(time.time()), 0, uid))
    close()
    return {'username': username, 'fullname': fullname, 'lastlogin': lastlogin}
  else:
    query = 'UPDATE users SET tries = %s WHERE id = %s'
    cur.execute(query, (tries + 1, uid))
    log(2, 'Wrong username or password') #TODO
    close()
    return None

