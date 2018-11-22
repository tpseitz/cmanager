# Encoding: UTF-8
import crypt, hmac, time, re
import MySQLdb
HOSTNAME, USERNAME, PASSWORD, DATABASE = 'localhost', None, None, None
MAX_TRIES = 5

REGEX_USERNAME = re.compile(r'^[a-z][a-z\d]+$')
#REGEX_FULLNAME = re.compile(r'^[A-Z][a-z]+( [A-Z][a-z]*){,3}$')
REGEX_FULLNAME = re.compile(r'^[^\d"\';\\]+$')
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

  if not (HOSTNAME and USERNAME and PASSWORD and DATABASE):
    log(0, 'No database configuration')

__CONNECTION = None
def _cursor():
  global HOSTNAME, USERNAME, PASSWORD, DATABASE, __CONNECTION

  if not (HOSTNAME and USERNAME and PASSWORD and DATABASE):
    log(0, 'Database not configured')

  if not __CONNECTION:
    __CONNECTION = MySQLdb.connect(HOSTNAME, USERNAME, PASSWORD, DATABASE)
  return __CONNECTION.cursor()

def close():
  global HOSTNAME, USERNAME, PASSWORD, DATABASE, __CONNECTION

  if __CONNECTION:
    __CONNECTION.commit()
    __CONNECTION.close()
  __CONNECTION = None

def listAccounts():
  cur = _cursor()
  names = ['id','tries','username','level','fullname','lastlogin']
  query = 'SELECT id,tries,username,level,fullname,lastlogin' \
    + ' FROM users;'
  cur.execute(query)
  rows = cur.fetchall()

  return [ dict(zip(names, row)) for row in rows ]

def createUser(username, fullname, level, password):
  username = username.lower()
  if not REGEX_USERNAME.match(username):
    log(0, 'Illegal username: %s' % (username,))
    return False

  if not REGEX_FULLNAME.match(fullname):
    log(0, 'Illegal username: %s' % (fullname,))
    return False

  level = int(level)

  if len(password) < 3:
    log(0, 'Password too short')
    return False
  password = crypt.crypt(password)

  cur = _cursor()
  query = 'SELECT id FROM users WHERE username = %s'
  cur.execute(query, (username,))
  if len(cur.fetchall()) > 0:
    log(0, 'User allready in database')
    return False

  cur = _cursor()
  query = 'INSERT INTO users (username, fullname, level, password)' \
    + ' VALUES (%s, %s, %s, %s)'
  cur.execute(query, (username, fullname, level, password))
  rows = cur.fetchall()

  uid = __CONNECTION.insert_id()
  if uid:
    close()
    return True

  return False

def removeUser(username):
  if not username: return False

  cur = _cursor()
  query = 'DELETE FROM users WHERE username = %s'
  cur.execute(query, (username,))
  close()

  return True

def checkPassword(username, password):
  username = username.lower()
  if not REGEX_USERNAME.match(username):
    log(1, 'Illegal username: %s' % (username,))
    return None

  cur = _cursor()
  query = 'SELECT id, password, tries, username, level, fullname, lastlogin' \
    + ' FROM users WHERE username = %s'
  cur.execute(query, (username,))
  rows = cur.fetchall()

  if len(rows) != 1:
    if len(rows) > 1: log(0, 'Database error: More than one result')
    else: log(2, 'Wrong username or password') #TODO
    return None
  uid, pwhash, tries, username, level, fullname, lastlogin = rows[0]

  if tries > MAX_TRIES:
    log(2, 'This account is locked')
    return None

  hsh = crypt.crypt(password, pwhash)
  if hmac.compare_digest(hsh, pwhash):
    query = 'UPDATE users SET lastlogin = %s, tries = %s WHERE id = %s'
    cur.execute(query, (int(time.time()), 0, uid))
    close()
    return {'username': username, 'level': level,
      'fullname': fullname, 'lastlogin': lastlogin}
  else:
    query = 'UPDATE users SET tries = %s WHERE id = %s'
    cur.execute(query, (tries + 1, uid))
    log(2, 'Wrong username or password') #TODO
    close()
    return None

