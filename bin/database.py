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

import datetime, crypt, hmac, time, re
import MySQLdb
HOSTNAME, USERNAME, PASSWORD, DATABASE = 'localhost', None, None, None
LOG_TIME_FORMAT, MAX_TRIES = '%Y-%m-%d %H:%M:%S ', 5
LEVELS = ['ERR', 'WAR', 'NFO', 'NFO', 'DBG']

REGEX_USERNAME = re.compile(r'^[a-z][a-z\d]+$')
#REGEX_FULLNAME = re.compile(r'^[A-Z][a-z]+( [A-Z][a-z]*){,3}$')
REGEX_FULLNAME = re.compile(r'^[^\d"\';\\]+$')
REGEX_ESCAPE = re.compile(r'["\';\\]')

def log(lvl, message, extra=None):
  timestamp = datetime.datetime.now().strftime(LOG_TIME_FORMAT)
  if lvl >= len(LEVELS): lvl = len(LEVELS) - 1
  print('%s[%s] %s' % (timestamp, LEVELS[lvl], message))
  if extra is not None: print('  %r' % (extra,))

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
    try:
      __CONNECTION = MySQLdb.connect(HOSTNAME, USERNAME, PASSWORD, DATABASE)
    except MySQLdb.OperationalError as oe:
      log(0, 'Could not connect to database: %s' % (oe.args[1],))
  return __CONNECTION.cursor()

def close():
  global __CONNECTION

  if __CONNECTION:
    __CONNECTION.commit()
    __CONNECTION.close()
  __CONNECTION = None

def _createWhere(where, data):
  wq, ao = '', True
  for wd in where:
    if   isinstance(wd, str) and wd.lower() in ('and', 'or'):
      wq += ' %s ' % wd.upper()
      ao = True
    elif isinstance(wd, (tuple, list)) and len(wd) == 2 \
        and wd[1].lower() in ('null', 'not null', '!null'):
      col, arg = wd
      if arg == '!null': arg = 'not null'
      wq += '%s IS %s' % (col, arg.upper())
    elif isinstance(wd, (tuple, list)) and len(wd) == 3 \
        and isinstance(wd[2], (tuple, list)):
      col, opr, dt = wd
      if opr == 'in':
        wq += '%s IN (%s)' % (col, ','.join(map(str, dt)))
      elif opr == 'not in':
        wq += '%s NOT IN (%s)' % (col, ','.join(map(str, dt)))
      else: raise ValueError(
        'Illegal comparison operator for where clause: %s' % (opr,))
    elif isinstance(wd, (tuple, list)) and len(wd) == 3:
      #TODO Check where clause for illegal names
      col, opr, dt = wd
      if opr not in ('==','<=','>=','<','>','!='): raise ValueError(
        'Illegal comparison operator for where clause: %s' % (opr,))
      if opr == '==': opr = '='
      if not ao: wq += ' AND '
      wq += '%s %s %%s' % (col, opr)
      data.append(dt)
      ao = False
    else: raise ValueError('Unknown where statement: %r' % (wd,))
  return ' WHERE ' + wq

def select(table, columns=None, where=None, order=None):
  #TODO Check table for illegal names
  if columns is not None:
    columns = ','.join(columns)
    #TODO Check columns for illegal names
  else: columns = '*'
  query = 'SELECT %s FROM %s' % (columns, table)
  data = []
  if where is not None: query += _createWhere(where, data)
  if order is not None:
    if not isinstance(order, (list, tuple)): order = [order]
    _order = []
    for cn in order:
      if cn[0] == '-': cn = cn[1:] + ' DESC'
      _order.append(cn)
    #TODO Check order fields for illegal names
    query += ' ORDER BY %s' % ','.join(_order)

  cur = _cursor()
  if not data: cur.execute(query)
  else: cur.execute(query, data)
  rows = cur.fetchall()

  names = [c[0] for c in cur.description]
  return [dict(zip(names, row)) for row in rows]

def insert(table, values):
  if len(values) == 0: return False

  data, cn = [], []
  for k, v in values.items():
    cn.append(k)
    data.append(v)

  query = 'INSERT INTO %s (%s)' % (table, ', '.join(cn))
  query += ' VALUES (%s)' % ', '.join(['%s' for i in range(len(data))])

  cur = _cursor()
  cur.execute(query, data)

  return __CONNECTION.insert_id()

def update(table, values, where):
  if len(values) == 0 or len(where) == 0: return False

  data, dr, wr = [], [], []
  for k, v in values.items():
    dr.append('%s = %%s' % (k,))
    data.append(v)
  for k, v in where.items():
    wr.append('%s = %%s' % (k,))
    data.append(v)

  query = 'UPDATE %s' % (table,)
  query += ' SET ' + ', '.join(dr)
  query += ' WHERE ' + ' AND '.join(wr)

#  raise Exception('%s <= %r' % (query, data)) #XXX

  cur = _cursor()
  cur.execute(query, data)

  return True

def delete(table, where):
  if not isinstance(where, dict) or len(where) == 0: return False

  #TODO Check table and fields for illegal names

  data, wc = [], []
  for k, v in where.items():
    wc.append('%s = %%s' % (k,))
    data.append(v)
  query = 'DELETE FROM %s' % (table,)
  query += ' WHERE ' + ' AND '.join(wc)

  cur = _cursor()
  cur.execute(query, data)

  return True

def listAccounts():
  cur = _cursor()
  names = ['uid','tries','username','level','fullname','lastlogin']
  query = 'SELECT %s FROM users;' % ','.join(names)
  cur.execute(query)
  rows = cur.fetchall()

  return [ dict(zip(names, row)) for row in rows ]

def createUser(username, fullname, level, password):
  username = username.lower()
  if not REGEX_USERNAME.match(username):
    log(0, 'ERR_ILLEGAL_USERNAME', username)
    return False

  if not REGEX_FULLNAME.match(fullname):
    log(0, 'ERR_ILLEGAL_FULLNAME', fullname)
    return False

  level = int(level)

  if len(password) < 3:
    log(0, 'ERR_PASSWORD_TOO_SHORT')
    return False
  password = crypt.crypt(password)

  cur = _cursor()
  cur.execute('SELECT uid FROM users WHERE username = %s', (username,))
  if len(cur.fetchall()) > 0:
    log(0, 'ERR_USER_ALLREADY_EXISTS', username)
    return False

  cur.execute('SELECT uid FROM users WHERE fullname = %s', (fullname,))
  if len(cur.fetchall()) > 0:
    log(0, 'ERR_USER_ALLREADY_EXISTS', fullname)
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

def updatePassword(username, newpass, oldpass=None):
  cur = _cursor()
  query = 'SELECT uid, password FROM users WHERE username = %s'
  cur.execute(query, (username,))
  rows = cur.fetchall()
  if len(rows) != 1:
    log(2, 'User %s does not exist' % username)
    return { '_error': ('ERR_USER_DOES_NOT_EXIST', (username,)) }

  uid, pwhash = rows[0]
  if oldpass is not None:
    hsh = crypt.crypt(newpass, pwhash)
    if not hmac.compare_digest(hsh, pwhash):
      log(2, 'Wrong password')
      return { '_error': 'ERR_WRONG_PASSWORD' }

  if len(password) < 3:
    log(2, 'Password too short')
    return { '_error': 'ERR_PASSWORD_TOO_SHORT' }
  password = crypt.crypt(newpass)

  query = 'UPDATE users SET password = %s, tries = %s WHERE uid = %s'
  cur.execute(query, (password, 0, uid))
  close()
  return {}

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
    return { 'username': None, 'level': -1, '_error': 'MSG_ILLEGAL_USERNAME' }

  cur = _cursor()
  query = 'SELECT uid, password, tries, username, level, fullname, lastlogin' \
    + ' FROM users WHERE username = %s'
  cur.execute(query, (username,))
  rows = cur.fetchall()

  if len(rows) != 1:
    if len(rows) > 1: log(0, 'Database error: More than one result')
    return { 'username': None, 'level': -1, '_error': 'MSG_LOGIN_FAILED' }
  uid, pwhash, tries, username, level, fullname, lastlogin = rows[0]

  if tries > MAX_TRIES:
    log(2, 'This account is locked')
    return { 'username': None, 'level': -1, '_error': 'MSG_ACCOUNT_LOCKED' }

  hsh = crypt.crypt(password, pwhash)
  if hmac.compare_digest(hsh, pwhash):
    query = 'UPDATE users SET lastlogin = %s, tries = %s WHERE uid = %s'
    cur.execute(query, (int(time.time()), 0, uid))
    close()
    return { 'username': username, 'level': level,
      'fullname': fullname, 'lastlogin': lastlogin }
  else:
    query = 'UPDATE users SET tries = %s WHERE uid = %s'
    cur.execute(query, (tries + 1, uid))
    log(2, 'Wrong password')
    close()
    return { 'username': None, 'level': -1, '_error': 'MSG_LOGIN_FAILED' }

