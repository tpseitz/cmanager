# Encoding: UTF-8
import re
import database

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

_COMPUTERS, _COMPUTERS_PER_CID = [], {}
def listComputers():
  global _COMPUTERS, _COMPUTERS_PER_CID

  if not _COMPUTERS:
    _COMPUTERS = database.select('computers', order='name')
    _COMPUTERS_PER_CID = { c['cid']: c for c in _COMPUTERS }

  return _COMPUTERS

def getComputer(search):
  listComputers()

  if isinstance(search, str) and REGEX_INTEGER.match(search):
    search = int(search)

  if   isinstance(search, int): return _COMPUTERS_PER_CID.get(search)
  elif isinstance(search, str): return _COMPUTERS_PER_CID.get(search)
  else: raise TypeError('Illegal type for computer search: %r' % type(search))

_PERSONS, _PERSONS_PER_PID = [], {}
def listUsers(computer_id=None, shift_id=None):
  global _PERSONS, _PERSONS_PER_PID

  if not _PERSONS:
    listShifts()
    listComputers()
    _PERSONS = database.select('persons', order='name')
    for p in _PERSONS:
      dn, pr = [], []
      p['presence'], p['day_names'] = [], []
      for di, dn in enumerate(lang['WORKDAYS']):
        if p['day_%d' % di]:
          p['presence'].append((di, lang['DAY_NAMES'][di], True))
          p['day_names'].append(dn)
        else:
          p['presence'].append((di, lang['DAY_NAMES'][di], False))
      if p['computer_id'] is None:
        p.update({ 'status': None, 'computer_name': None })
      else:
        p.update({ 'status': 'active',
          'computer_name': _COMPUTERS_PER_CID[p['computer_id']]['name'] })

      if p['shift_id'] is None:
        p.update({ 'shift_name': None, 'shift_ord': None })
      else:
        s = _SHIFTS_PER_SID[p['shift_id']]
        p.update({ 'shift_name': s['name'], 'shift_ord': s['ord'] })

      if p['computer_id'] is not None:
        p['computer'] = _COMPUTERS_PER_CID[p['computer_id']]['name']

    _PERSONS_PER_PID = { p['pid']: p for p in _PERSONS}

  pl = _PERSONS

  if computer_id is not None:
    pl = [p for p in pl if p['computer_id'] == computer_id]
  if shift_id is not None:
    pl = [p for p in pl if p['shift_id'] == shift_id]

  return pl

def getUser(search):
  listUsers()

  if isinstance(search, str) and REGEX_INTEGER.match(search):
    search = int(search)

  if   isinstance(search, int): return _PERSONS_PER_PID.get(search)
  elif isinstance(search, str): return _PERSONS_PER_PID.get(search)
  else: raise TypeError('Illegal type for user search: %r' % type(search))

