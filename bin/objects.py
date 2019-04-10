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

import collections, datetime, re
import database

FORMAT_DATE = '%Y-%m-%d'
ALERT_DAYS_START, ALERT_DAYS_END_RED, ALERT_DAYS_END_YELLOW = 7, 14, 28

MAX_NAME_SIZE = 64

REGEX_STRIP = re.compile(r'[^A-Za-z\d]')
REGEX_INTEGER = re.compile(r'^\s*-?\s*\d+\s*$')

lang = {}

def strip(message):
  return REGEX_STRIP.sub('', message.lower())

def log(lvl, message, *extra):
  print(message)

_SHIFTS, _SHIFTS_PER_ORD, _SHIFTS_PER_SID, _SHIFTS_PER_NM = [], {}, {}, {}
def listShifts():
  global _SHIFTS, _SHIFTS_PER_ORD, _SHIFTS_PER_SID, _SHIFTS_PER_NM

  if not _SHIFTS:
    _SHIFTS = database.select('shifts', order='ord')
    _SHIFTS_PER_ORD = { s['ord']: s for s in _SHIFTS }
    _SHIFTS_PER_SID = { s['sid']: s for s in _SHIFTS }
    _SHIFTS_PER_NM  = { strip(s['name']): s for s in _SHIFTS }

  return _SHIFTS

def getShift(search):
  listShifts()

  if isinstance(search, str) and REGEX_INTEGER.match(search):
    search = int(search)

  if   isinstance(search, int): return _SHIFTS_PER_SID.get(search)
  elif isinstance(search, str): return _SHIFTS_PER_NM.get(search)
  else: raise TypeError('Illegal type for shift search: %r' % type(search))

def addShift(name, max_users, description):
  max_users = int(max_users)
  description = description.strip()
  if not description: description = None
  place = max([s['ord'] for s in listShifts()]) + 1
  database.insert('shifts', { 'ord': place, 'name': name,
    'max_users': max_users, 'description': description })

  return None

def deleteShift(shift_id):
  pc = len(database.select('persons', where=[('shift_id', '==', shift_id)]))
  if pc > 0: return 'ERR_SHIFT_HAS_USERS'

  database.delete('shifts', { 'sid': shift_id })
  return None

def moveShift(shift_id, down):
  ls = listShifts()
  if down: ls = reversed(ls)

  prev, this = None, None
  for s in ls:
    if s['sid'] == shift_id:
      this = s
      break
    else: prev = s

  if not (prev and this):
    raise Exception('Shift %d seems to be in the edge' % (shift_id,))

  database.update('shifts', { 'ord': 0 }, { 'sid': prev['sid'] })
  database.update('shifts', { 'ord': prev['ord'] }, { 'sid': this['sid'] })
  database.update('shifts', { 'ord': this['ord'] }, { 'sid': prev['sid'] })

_COMPUTERS, _COMPUTERS_PER_CID = [], {}
def listComputers():
  global _COMPUTERS, _COMPUTERS_PER_CID

  if not _COMPUTERS:
    _COMPUTERS = database.select('computers', order='name')
    _COMPUTERS_PER_CID = { c['cid']: c for c in _COMPUTERS }

  return _COMPUTERS

def getComputer(search, is_name=False):
  listComputers()

  if not is_name and isinstance(search, str) and REGEX_INTEGER.match(search):
    search = int(search)

  if   isinstance(search, int): return _COMPUTERS_PER_CID.get(search)
  elif isinstance(search, str): return _COMPUTERS_PER_CID.get(search)
  else: raise TypeError('Illegal type for computer search: %r' % type(search))

def moveComputer(search, x, y):
  cpu = getComputer(search)
  if cpu is None: return False

  database.update('computers', { 'x': x, 'y': y }, { 'cid': cpu['cid'] })

  return True

def createComputer(name):
  global _COMPUTERS, _COMPUTERS_PER_CID
  _COMPUTERS, _COMPUTERS_PER_CID = [], {}

  if len(name) > MAX_NAME_SIZE: name = name[:MAX_NAME_SIZE]
  cid = database.insert('computers', { 'name': name })
  if not cid: return None
  return getComputer(cid)

def deleteComputer(search):
  cpu = getComputer(search)
  if cpu is None: return 'ERR_NO_COMPUTER'

  uls = listPersons(cpu['cid'])
  if len(uls) > 0: return 'ERR_COMPUTER_HAS_USERS'

  rc = database.delete('computers', { 'cid': cpu['cid'] })

  if rc: return None
  else: return 'ERR_DELETE'

def listVacant(shift):
  els = set([u['computer_id'] for u in listPersons(shift_id=shift)])
  cls = [c for c in listComputers() if c['cid'] not in els]
  return cls

_COACHES, _COACHES_PER_ID = [], {}
def listCoaches():
  global _COACHES, _COACHES_PER_ID

  if not _COACHES_PER_ID:
    _COACHES = database.select('coaches', order='name')
    _COACHES_PER_ID = { c['oid']: c for c in _COACHES }

  return _COACHES

def getCoach(search, create=False):
  global MAX_NAME_SIZE, _COACHES, _COACHES_PER_ID

  listCoaches()

  if isinstance(search, int): return _COACHES_PER_ID.get(search)

  if len(search) > MAX_NAME_SIZE: search = search[:MAX_NAME_SIZE]

  for ch in _COACHES:
    if ch['name'] == search: return ch

  if not create: return None

  database.insert('coaches', { 'name': search })
  saveData()

  _COACHES, _COACHES_PER_ID = [], {}

  return getCoach(search)

def deleteCoach(coach_id):
  pc = len(database.select('persons', where=[('coach_id', '==', coach_id)]))
  if pc > 0: return 'ERR_COACH_HAS_USERS'

  database.delete('coaches', { 'oid': coach_id })
  return None

def _updatePerson(person):
  global FORMAT_DATE, ALERT_DAYS_START, _COACHES_PER_ID, \
    ALERT_DAYS_END_RED, ALERT_DAYS_END_YELLOW

  dn, pr = [], []
  person['presence'], person['day_names'] = [], []
  for di, dn in enumerate(lang['WORKDAYS']):
    if person['day_%d' % di]:
      person['presence'].append((di, lang['DAY_NAMES'][di], True))
      person['day_names'].append(dn)
    else:
      person['presence'].append((di, lang['DAY_NAMES'][di], False))
  if person['computer_id'] is None:
    person.update({ 'status': None, 'computer_name': None })
  else:
    person.update({ 'status': 'active',
      'computer_name': _COMPUTERS_PER_CID[person['computer_id']]['name'] })

  if not person['comments']: person['comments'] = ''
  if not person['coach_id']: person['coach_name'] = ''
  else: person['coach_name'] = getCoach(person['coach_id'])['name']

  if person['shift_id'] is None:
    person.update({ 'shift_name': None, 'shift_ord': None })
  else:
    s = getShift(person['shift_id'])
    person.update({ 'shift_name': s['name'], 'shift_ord': s['ord'] })

  if person['computer_id'] is not None:
    person['computer'] = _COMPUTERS_PER_CID[person['computer_id']]['name']

  person['start_date_string'], person['end_date_string'] = '', ''
  person['days_to_start'], person['days_to_end'] = None, None
  person['days_to_year'] = None
  person['ended'] = False
  dt = datetime.date.today().toordinal()
  if person['start_date']:
    person['start_date_string'] \
      = datetime.date.fromordinal(person['start_date']).strftime(FORMAT_DATE)
    person['days_to_start'] = person['start_date'] - dt
    if person['days_to_start'] <= 0: person['days_to_start'] = None
    elif person['days_to_start'] < ALERT_DAYS_START:
      person['hilight'] = 'tostart'
  else:
    person['start_date_string'] = ''

  if person['end_date']:
    person['end_date_string'] \
      = datetime.date.fromordinal(person['end_date']).strftime(FORMAT_DATE)
    if person['end_date'] < dt: person['ended'] = True

    person['days_to_end']  = person['end_date']   - dt
    person['days_to_year'] = person['start_date'] - dt + 365
    if person['days_to_end'] < 0:  person['days_to_end'] = None
    elif person['days_to_end'] < ALERT_DAYS_END_RED:
      person['hilight'] = 'red'
    elif person['days_to_end'] < ALERT_DAYS_END_YELLOW:
      person['hilight'] = 'yellow'
    if person['days_to_year'] < 0: person['days_to_year'] = None
  else:
    person['end_date_string'] = ''

  return person

_QUEUE = []
def listQueue():
  global _QUEUE

  if not _QUEUE:
    dt = datetime.date.today().toordinal()
    where = [('start_date', '>', dt), 'or', ('start_date', 'null')]
    order = ['--start_date', 'created']
    _QUEUE = database.select('persons', where=where, order=order)
    count = 1
    for p in _QUEUE:
      _updatePerson(p)
      p['ord'] = count
      count += 1

    _PERSONS_PER_PID.update({ p['pid']: p for p in _QUEUE })

  return _QUEUE

_PERSONS, _PERSONS_PER_PID = [], {}
def listPersons(computer_id=None, shift_id=None):
  global _PERSONS, _PERSONS_PER_PID

  if not _PERSONS:
    listShifts()
    listComputers()
    dt = datetime.date.today().toordinal()
    where = [('start_date', '<=', dt), 'and', ('end_date', '>=', dt)]
    _PERSONS = database.select('persons', where=where, order='name')
    for p in _PERSONS: _updatePerson(p)

    _PERSONS_PER_PID.update({ p['pid']: p for p in _PERSONS })

  pl = _PERSONS

  if computer_id is not None:
    pl = [p for p in pl if p['computer_id'] == computer_id]
  if shift_id is not None:
    pl = [p for p in pl if p['shift_id'] == shift_id]

  return pl

def getPerson(search):
  listPersons()
  listQueue()

  if isinstance(search, str) and REGEX_INTEGER.match(search):
    search = int(search)

  if isinstance(search, int): return _PERSONS_PER_PID.get(search)
  else: raise TypeError('Illegal type for user search: %r' % type(search))

def createPerson(name, start_date, end_date, shift, days):
  global _PERSONS, _PERSONS_PER_PID
  _PERSONS, _PERSONS_PER_PID = [], {}

  start_date = datetime.datetime.strptime(start_date, FORMAT_DATE).date()
  end_date   = datetime.datetime.strptime(end_date, FORMAT_DATE).date()

  #TODO Check person name for illegal characters
  shift = int(shift)
  days = set(map(int, days))

  if len(name) > MAX_NAME_SIZE: name = name[:MAX_NAME_SIZE]
  data = collections.OrderedDict((
    ('name', name), ('start_date', start_date.toordinal()),
    ('end_date', end_date.toordinal()), ('shift_id', shift)))
  for i in range(len(lang['WORKDAYS'])): data['day_%d' % i] = i in days

  uid = database.insert('persons', data)

  if uid: return getPerson(uid)
  else: return None

def deletePerson(search):
  usr = getPerson(search)

  if usr is None: return 'ERR_NO_PERSON'

  rc = database.delete('persons', { 'pid': usr['pid'] })

  if rc: return None
  else: return 'ERR_DELETE'

def setDates(person, start_date, end_date):
  person = int(person)
  start_date = datetime.datetime.strptime(start_date, FORMAT_DATE).date()
  end_date   = datetime.datetime.strptime(end_date, FORMAT_DATE).date()

  data = collections.OrderedDict({
    'start_date': start_date.toordinal(), 'end_date': end_date.toordinal() })
  database.update('persons', data, { 'pid': person })

def assignShift(person, shift=None, days=[]):
  person = int(person)
  shift = int(shift)
  days = set(map(int, days))

  data = collections.OrderedDict()

  shf = getShift(shift)
  if shift is not None and shf is None: return False
  data['shift_id'] = shf['sid']

  for i in range(len(lang['WORKDAYS'])): data['day_%d' % i] = i in days

  return database.update('persons', data, { 'pid': person })

def assignCoach(person, coach, create=False):
  usr = getPerson(person)
  if usr is None: return False

  ch = { 'oid': None, 'name': '' }
  if coach: ch = getCoach(coach, create)

#  raise Exception('%r' % (ch,))
  database.update('persons',
    { 'coach_id': ch['oid'] }, { 'pid': usr['pid'] })

  return True

def setComment(person, comment):
  usr = getPerson(person)
  if usr is None: return False

  comment = comment.strip()
  if not comment: comment = None

  database.update('persons', { 'comments': comment }, { 'pid': usr['pid'] })

  return True

def assignComputer(person, computer=None):
  usr = getPerson(person)
  if usr is None: return ()

  if computer is not None:
    for cu in listPersons(computer, usr['shift_id']):
      if cu is not None:
        if cu['pid'] == usr['pid']: return True
        else: return False

  if computer is None or computer == 'NULL':
    cpu, cid = None, None
  else:
    cpu = getComputer(computer)
    if cpu is None: return ()
    cid = cpu['cid']

  database.update('persons', { 'computer_id': cid }, { 'pid': usr['pid'] })

  if cpu is not None: return cpu['name'],  usr['name']
  else: return (usr['name'],)

def saveData():
  database.close()

