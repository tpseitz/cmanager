# Encoding: UTF-8
import re
import database
_SHIFTS, _SHIFTS_PER_ORD, _SHIFTS_PER_SID = [], {}, {}

REGEX_STRIP = re.compile(r'[^A-Za-z\d]')
REGEX_INTEGER = re.compile(r'^\s*-?\s*\d+\s*$')

lang = {}

def strip(message):
  return REGEX_STRIP.sub('', message.lower())

def log(lvl, message, *extra):
  print(message)

def listShifts():
  global _SHIFTS, _SHIFTS_PER_ORD, _SHIFTS_PER_SID

  if not _SHIFTS:
    _SHIFTS = database.select('shifts', order='ord')
    _SHIFTS_PER_ORD = { s['ord']: s for s in _SHIFTS }
    _SHIFTS_PER_SID = { s['sid']: s for s in _SHIFTS }

  return _SHIFTS

def getShift(search):
  listShifts()

  if isinstance(search, str) and REGEX_INTEGER.match(search):
    search = int(search)

  if   isinstance(search, int): return _SHIFTS_PER_ORD.get(search)
  elif isinstance(search, str): return _SHIFTS_PER_SID.get(search)
  else: raise TypeError('Illegal type for shift search: %r' % type(search))

_COMPUTERS, _COMPUTERS_PER_CID = [], {}
def listComputers():
  global _COMPUTERS, _COMPUTERS_PER_CID

  if not _COMPUTERS:
    _COMPUTERS = database.select('computers', order='name')
    _COMPUTERS_PER_CID = { c['cid']: c for c in _COMPUTERS }

  return _COMPUTERS

_PERSONS = []
def listUsers(computer_id=None, shift_id=None):
  global _PERSONS

  if not _PERSONS:
    listShifts()
    listComputers()
    _PERSONS = database.select('persons', order='name')
    for p in _PERSONS:
      dn, pr = [], []
      p['presence'], p['day_names'] = [], []
      for di, dn in enumerate(lang['WORKDAYS']):
        if p['day_%d' % di]:
          p['presence'].append(True)
          p['day_names'].append(dn)
        else:
          p['presence'].append(False)
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

  pl = _PERSONS

  if computer_id is not None:
    return [p for p in pl if p['computer_id'] == computer_id]

  return pl

