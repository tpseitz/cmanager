# Encoding: UTF-8
import json, re, os
DIRECTORY = None
ROOMS, SHIFT_NAMES, SHIFTS = [], [], 0
SHIFT_PROPERTIES = []

REGEX_STRIP = re.compile(r'[^A-Za-z\d]')

lang = {}

def strip(message):
  return REGEX_STRIP.sub('', message.lower())

def log(lvl, message, *extra):
  print(message)

class Computer(object):
  _COMPUTERS = {}

  def fromDict(data):
    return Computer(data.get('name'),
      data.get('room'),
      data.get('location'))

  def __init__(self, data, room=None, location=None):
    self.name = data
    self.room = room
    self.location = location
    self.cid = REGEX_STRIP.sub('', self.name.lower())

    self.users = []

    if self.cid in Computer._COMPUTERS:
      log(0, lang['ERR_DUPLICATE_COMPUTER'] % (self.name,))
    else: Computer._COMPUTERS[self.cid] = self

  def __str__(self):
    if self.room and self.location:
      return '%s: %s %r' % (self.name, self.room, self.location)
    else:
      return '%s: %s' % (self.name, lang['NO_LOCATION'])

  def toDict(self):
    tmp = { 'cid': self.cid, 'name': self.name,
      'room': self.room, 'location': self.location }
    if self.location:
      tmp.update({ 'x': self.location[0], 'y': self.location[1] })
    return tmp

class User(object):
  _USERS = {}
  _CONNECTIONS = set()

  def fromDict(data):
    return User(data.get('name'),
      data.get('shift'),
      data.get('days'),
      data.get('computer'))

  def __init__(self, name, shift=None, days=None, computer=None):
    self.name = name
    self.shift = shift or 0
    self.days = sorted(set(days or []))
    self.uid = REGEX_STRIP.sub('', self.name.lower())
    self.computer = computer

    if not 0 <= self.shift <= SHIFTS:
      log(0, lang['ERR_ILLEGAL_SHIFT'] % self.shift, (SHIFT_NAMES, SHIFTS))
      self.shift, self.days = 0, []
    elif self.days and (min(self.days) < 0 or max(self.days) > 4):
      log(0, lang['ERR_ILLEGAL_DAYS'] % (self.days,))
      self.shift, self.days = 0, []

    if isinstance(self.computer, str):
      if self.computer in Computer._COMPUTERS:
        self.computer = Computer._COMPUTERS[self.computer]
      else: self.computer = None

    if self.uid in User._USERS:
      log(0, lang['ERR_DUPLICATE_USER'] % self.name)
    else:
      User._USERS[self.uid] = self

    if self.shift and self.computer:
      if (self.shift, self.computer) in User._CONNECTIONS:
        log(0, lang['ERR_DUPLICATE_SEAT'] \
          % (SHIFT_NAMES[self.shift-1], self.computer))
      else:
        self.computer.users.append(self)
        User._CONNECTIONS.add((self.shift, self.computer.cid))

  def assignShift(self, shift, days):
    days = sorted(set(days))
    if not 0 < shift <= SHIFTS:
      log(0, lang['ERR_ILLEGAL_SHIFT'] % (shift,))
      return False
    if min(days) < 0 or max(days) > 4:
      log(0, lang['ERR_ILLEGAL_DAYS'] % (days,))
      return False
    if self.computer:
      User._CONNECTIONS.remove((self.shift, self.computer.cid))
      self.computer.users.remove(self)
    self.shift = shift
    self.days = days
    if self.computer:
      if self.shift in [t[0] for t in User._CONNECTIONS]:
        self.computer = None
    return True

  def assignComputer(self, computer):
    if not computer:
      self.computer = None
      return True

    computer = REGEX_STRIP.sub('', computer.lower())
    if computer not in Computer._COMPUTERS:
      log(0, lang['ERR_UNKNOWN_COMPUTER'] % (computer,))
      return False
    if not (self.shift and self.days):
      log(0, lang['ERR_NO_SHIFT'])
      return False
    if (self.shift, computer) in User._CONNECTIONS:
      log(0, lang['ERR_SEAT_TAKEN'])
      return False

    User._CONNECTIONS.add((self.shift, computer))
    self.computer = Computer._COMPUTERS[computer]
    self.computer.users.append(self)
    return True

  def __str__(self):
    if self.shift and self.days:
      return '%s: %s (%s) %s' % (self.name, SHIFT_NAMES[self.shift - 1],
        ' '.join([lang['WORKDAYS'][i] for i in self.days]),
        self.computer and self.computer.name or lang['NO_SEAT'])
    else:
      return '%s: %s' % (self.name, lang['NO_SHIFT'])

  def toDictBare(self):
    return { 'name': self.name, 'shift': self.shift, 'days': self.days,
      'computer':  self.computer and self.computer.cid or None }

  def toDict(self):
    tmp = self.toDictBare()
    tmp.update({ 'uid': self.uid, 'username': self.name,
      'day_names': [lang['WORKDAYS'][d] for d in self.days],
      'presence': [(d, lang['DAY_NAMES'][d], d in self.days and True or False)
        for d in range(5)],
      'status': self.computer and 'active' or None,
      'computer_name': self.computer and self.computer.name or None,
      'shift_name': SHIFT_NAMES[self.shift-1] })
    return tmp

def loadData():
  ffn = os.path.join(DIRECTORY, 'rooms.json')
  if os.path.isfile(ffn):
    with open(ffn, 'r') as f: ROOMS = json.loads(f.read())

  ffn = os.path.join(DIRECTORY, 'computers.json')
  if os.path.isfile(ffn):
    with open(ffn, 'r') as f:
      for dt in json.loads(f.read()): Computer.fromDict(dt)

  ffn = os.path.join(DIRECTORY, 'users.json')
  if os.path.isfile(ffn):
    with open(ffn, 'r') as f:
      for dt in json.loads(f.read()): User.fromDict(dt)

def saveData():
  ffn = os.path.join(DIRECTORY, 'computers.json')
  data = json.dumps(list(map(Computer.toDict, Computer._COMPUTERS.values())))
  with open(ffn, 'w') as f: f.write(data)

  ffn = os.path.join(DIRECTORY, 'users.json')
  data = json.dumps(list(map(User.toDict, User._USERS.values())))
  with open(ffn, 'w') as f: f.write(data)

def printData():
  for nm, cpu in Computer._COMPUTERS.items():
    print(cpu)
    for nm, usr in sorted(User._USERS.items(), key=lambda p: p[1].shift):
      if usr.computer == cpu: print('  ' + str(usr))

  print()
  for nm, usr in User._USERS.items():
    if usr.computer: continue
    print(usr)

#  for sh, cpu in User._CONNECTIONS: print('%8s %s' % (SHIFT_NAMES[sh-1], cpu))

def addShift(usr, shift, days):
  usr = REGEX_STRIP.sub('', usr.lower())
  if usr not in User._USERS:
    log(0, lang['ERR_UNKNOWN_USER'] % (usr,))
    return
  usr = User._USERS[usr]

  if shift not in SHIFT_NAMES:
    log(0, lang['ERR_UNKNOWN_SHIFT'] % (shift,))
    return
  shift = { v: i for i, v in enumerate(SHIFT_NAMES) }[shift]

  if len(days) == 1 and ',' in days[0]: days = days[0].split(',')
  for d in days:
    if d not in lang['WORKDAYS']:
      print(lang['ERR_UNKNOWN_DAY'] % (d,))
      return
  tmp = { v: i for i, v in enumerate(lang['WORKDAYS']) }
  days = sorted(set([tmp[d] for d in days]))

  log(2, lang['MSG_ADD_SHIFT'] % (usr, SHIFT_NAMES[shift],
    ', '.join([lang['WORKDAYS'][d] for d in days])))
  usr.assignShift(shift + 1, days)

  saveData()

def delete(name):
  nm = REGEX_STRIP.sub('', name.lower())
  if   nm in Computer._COMPUTERS:
    name = Computer._COMPUTERS[nm].name
    log(2, lang['MSG_REMOVING_COMPUTER'] % name)
    del Computer._COMPUTERS[nm]
    return name
  elif nm in User._USERS:
    name = User._USERS[nm].name
    log(2, lang['MSG_REMOVING_USER'] % name)
    del User._USERS[nm]
    return name
  return None


