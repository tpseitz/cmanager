#!/usr/bin/env python3
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

import datetime, json, sys, os
import database, objects, hypertext, sykeit, web

FLOORPLAN, VIEWBOX = None, [0, 0, 100, 100]

lang = {}
log = web.log
objects.log = log

def init():
  global FLOORPLAN, VIEWBOX, lang

  conf = sykeit.init()

  lang = sykeit.lang

  FLOORPLAN = conf.get('floorplan', FLOORPLAN)
  VIEWBOX = conf.get('viewbox', VIEWBOX)

  hypertext.GLOBALS['floorplan'] = floorplan
  hypertext.GLOBALS['submenu'] = [
    { 'title': '{{lang.COMPUTERS}}', 'path': 'computers' },
    { 'title': '{{lang.USERS}}', 'path': 'users' },
    { 'title': '{{lang.MAP}}', 'path': 'floorplan' },
    { 'title': '{{lang.QUEUE}}', 'path': 'queue' },
    { 'title': '{{lang.SETTINGS}}', 'path': 'config' }]

  objects.lang = lang
  objects.FORMAT_DATE = hypertext.FORMAT_DATE
  objects.ALERT_DAYS_START=conf.get('alert_days_start',objects.ALERT_DAYS_START)
  objects.ALERT_DAYS_END_RED \
    = conf.get('alert_days_end_red', objects.ALERT_DAYS_END_RED)
  objects.ALERT_DAYS_END_YELLOW \
    = conf.get('alert_days_end_yellow', objects.ALERT_DAYS_END_YELLOW)

  hypertext.GLOBALS['list_days'] = enumerate(lang['WORKDAYS'])
  hypertext.GLOBALS['list_shifts'] \
    = [(s['sid'], s['name']) for s in objects.listShifts()]
  hypertext.GLOBALS['viewbox'] = ' '.join(map(str, VIEWBOX))

  if 'lang' in web.GET: web.COOKIES['lang'] = web.GET['lang']

def outputConfigPage():
  data = { 'languages': sykeit.listLanguages() }
  if web.POST:
    data['POST'] = web.POST #XXX

  hypertext.GLOBALS['scripts'].append('interface.js')

  data['time_format'] = objects.FORMAT_DATE
  data['alert_days_end_red'] = objects.ALERT_DAYS_END_RED
  data['alert_days_end_yellow'] = objects.ALERT_DAYS_END_YELLOW
  data['shifts'] = objects.listShifts()
  data['coaches'] = objects.listCoaches()
  for lo in data['languages']:
    if lo['id'] == sykeit.LANG: lo['selected'] = True

  web.outputPage(hypertext.frame('config', data))

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

def formData():
  if web.SESSION.get('level', -1) < 100: return

  name = web.POST.get('_form', '')
  message = 'ERR_UNKNOWN_FORM'
  if name == 'adduser':
    usr = objects.createPerson(
      web.POST['name'], web.POST['start_date'], web.POST['end_date'],
      int(web.POST['shift']), list(map(int, web.POST.get('days', []))))
    if usr is None:
      web.redirect('users', 3, lang['ERR_ADD_USER'] % (str(usr),))
    else:
      log(2, 'Created user %r' % (usr,))
      objects.saveData()
      web.redirect('user/%d' % usr['pid'], 1,
        lang['MSG_ADD_USER'] % (usr['name'],))
  elif name == 'updateuser':
    usr = objects.getPerson(web.POST['pid'])
    #TODO Do some error checking
    objects.setDates(usr['pid'],
      web.POST['start_date'], web.POST['end_date'])
    rc = objects.assignShift(usr['pid'],
      int(web.POST['shift']), map(int, web.POST.get('days', [])))
    if web.POST.get('cid'): objects.assignComputer(usr['pid'], web.POST['cid'])
    objects.setComment(usr['pid'], web.POST['comment'])
    objects.assignCoach(usr['pid'], web.POST['coach'], True)
    objects.saveData()
    web.redirect('user/%s' % web.POST['pid'], 1, 'MSG_DATA_UPDATED')
  elif name == 'addcomputer':
    if objects.getComputer(web.POST['name'], True) is not None:
      web.redirect('computers', 3, 'ERR_DUPLICATE_COMPUTER')
    cpu = objects.createComputer(web.POST['name'])
    if cpu is None:
      web.redirect('computers', 3, 'ERR_ADD_COMPUTER')
    else:
      log(2, 'Added computer %s into database' % (cpu['name'],))
      objects.saveData()
      web.redirect('computer/%d' % cpu['cid'],
        1, lang['MSG_ADD_COMPUTER'] % (cpu['name'],))
  elif name == 'addshift':
    name, users, desc = map(web.POST.get, ('name', 'max_users', 'description'))
    objects.addShift(name, users, desc)
    objects.saveData()
    web.redirect('config', 1, 'MSG_SHIFT_ADDED')
  elif name == 'config':
    conf = {}
    if web.POST.get('lang') != sykeit.LANG: conf['lang'] = web.POST['lang']
    if 'time_format' in web.POST:
      conf['time_format'] = web.POST['time_format']
    if 'alert_days_end_yellow' in web.POST:
      conf['alert_days_end_yellow'] = int(web.POST['alert_days_end_yellow'])
    if 'alert_days_end_yellow' in web.POST:
      conf['alert_days_end_red'] = int(web.POST['alert_days_end_red'])
    if 'alert_days_start' in web.POST:
      conf['alert_days_start'] = int(web.POST['alert_days_start'])
    if not conf: web.redirect('config', 1, 'MSG_NO_CHANGES')

    if not sykeit.CONF_FFN: raise Exception('No configuration file')
    if not sykeit.DATA_DIRECTORY: raise Exception('No data directory')
    ffn = os.path.join(sykeit.DATA_DIRECTORY, 'generated_config.json')
    with open(sykeit.CONF_FFN, 'r') as f: manual = json.loads(f.read())
    tffn = ffn + '.back'
    if os.path.isfile(tffn): raise Exception('File is being modified')
    if os.path.isfile(ffn):
      os.rename(ffn, tffn)
      with open(tffn, 'r') as f: tmp = json.loads(f.read())
      tmp.update(conf)
      conf = tmp

    dl = set()
    for k, v in conf.items():
      if k in manual and manual[k] == v: dl.add(k)
    for k in dl: del conf[k]
    #TODO check that settings can be reseted
    if not conf: web.redirect('config', 1, 'MSG_NO_CHANGES')

    with open(ffn, 'w') as f: f.write(json.dumps(conf))
    if os.path.isfile(tffn): os.unlink(tffn)
    web.redirect('config', 1, 'MSG_SETTINGS_SAVED')

  else: log(0, 'Unknown form: %s' % (name,))

  web.redirect(web.POST.get('_next', ''), 3, message)

web.handleForm = formData

BORDERS = 100
def floorplan(shift=None, selected=None):
  if isinstance(selected, str): selected = int(selected)
  data = { 'computers': [] }
  if shift is not None:
    shift = objects.getShift(shift)
    if shift is not None: data['shift_name'] = shift['name']
  yy = 30
  for cpu in objects.listComputers():
    tmp = cpu.copy()
    if not cpu['x']:
      tmp['x'], tmp['y'] = 15, yy
      yy += 32
    tmp['users'], cnt = [], 2
    sid = shift and shift['sid'] or None
    for usr in sorted(objects.listPersons(computer_id=cpu['cid'], shift_id=sid),
        key=lambda u: u['shift_ord']):
      usr = usr.copy()
      usr['line'] = cnt
      cnt += 1.5
      tmp['users'].append(usr)
    tmp['lines'] = max(cnt - 1, 2.5)
    if shift is None:
      if   len(tmp['users']) == 0: tmp['status'] = 'vacant'
      elif len(tmp['users']) < len(objects.listShifts()):
        tmp['status'] = 'partly'
      else: tmp['status'] = 'reserved'
    else: tmp['status'] = len(tmp['users']) and 'reserved' or 'vacant'
    if selected is not None and cpu['cid'] == selected:
      x, y = 0, 0
      if cpu['x']: x, y = cpu['x'], cpu['y']
      tmp['status'] = 'selected'
    data['computers'].append(tmp)
  if selected is not None:
    data['viewbox'] = ' '.join(map(str,
      [x - BORDERS, y - BORDERS, 2 * BORDERS, 2 * BORDERS]))
    data['class'] = 'area'
  if not (FLOORPLAN and os.path.isfile(FLOORPLAN)):
    log(0, 'Floorplan does not exist')
  with open(FLOORPLAN, 'r') as f: svg = f.read()

  return hypertext.frame('floorplan', data, svg)

def mainCGI():
  global FLOORPLAN

  path = web.startCGI(init)
  if len(path) == 0: path = ['computers']
  usr_lvl = web.SESSION.get('level', -1)

  hypertext.GLOBALS['session'] = web.SESSION

  data = {}

  if usr_lvl <= 0:
    web.outputPage(hypertext.frame('<div class="form">' \
      + hypertext.form('login', target='login') + '</div>'))

  # Compile shift status list
  data['shift_count'] = len(objects.listShifts())
  data['shift_users'] = []
  shifts = []
  for shf in objects.listShifts():
    shf = shf.copy()
    uls = objects.listPersons(shift_id=shf['sid'])
    user_count = len([u for u in uls])
    seated_users = len([u for u in uls if u['computer_id']])
    shf['shift_name'] = shf['name']
    shf['user_count'] = user_count
    shf['seated_users'] = seated_users
    if   seated_users  < shf['max_users']: shf['status'] = 'space'
    elif seated_users == shf['max_users']: shf['status'] = 'full'
    else: shf['status'] = 'overflow'
    data['shift_users'].append(shf)

    shifts.append({ 'shift_name': shf['shift_name'], 'sid': shf['sid'],
      'ord': shf['ord'], 'presence': 5 * [(None, None, True)],
      'name': shf['status']=="space" and '{{lang.VACANT}}' or '{{lang.FULL}}',
      'status': shf['status'] == "space" and 'free' or 'full' })

  # List coach names for auto complete
  data['coach_names'] = [c['name'] for c in objects.listCoaches()]

  # List computers and shifts under them with user info
  data['computers'], computers = [], {}
  for cpu in sorted(objects.listComputers(),
      key=lambda c: objects.strip(c['name'])):
    tmp = cpu.copy()
    uls = { u['shift_id']: u.copy() for u in objects.listPersons()
      if u['computer_id'] == tmp['cid'] }
    tmp['users'] = [s.copy() for s in shifts]
    for shf in tmp['users']:
      u = uls.get(shf['sid'])
      if u is not None: shf.update(u)
    data['computers'].append(tmp)
    computers[tmp['cid']] = tmp

  # List users
  data['users'] = [usr.copy() for usr in objects.listPersons()]

  # List queue
  data['queue'] = [usr.copy() for usr in objects.listQueue()]
  count = 1
  for usr in data['queue']:
    usr['ord'] = count
    count += 1

  if usr_lvl >= 50:
    if path[0] == 'user' and len(path) == 2 \
        and objects.REGEX_INTEGER.match(path[1]):
      data['user'] = objects.getPerson(path[1])
      if data['user'] is None: web.redirect('users', 3, 'NO_USER')
      web.outputPage(hypertext.frame('user', data))
    elif path[0] == 'computer' and len(path) == 2 \
        and objects.REGEX_INTEGER.match(path[1]):
      cid = int(path[1])
      data['computer'] = objects.getComputer(cid)
      data['computer']['users'] = objects.listPersons(computer_id=cid)
      web.outputPage(hypertext.frame('computer', data))
    elif path[0] == 'computers':
      cls, shift = [], None
      if len(path) == 2: shift = objects.getShift(objects.strip(path[1]))
#      raise Exception(objects._SHIFTS_PER_NM) #XXX

      for cpu in data['computers']:
        if shift is not None:
          cpu['user'] = [u for u in cpu['users'] if u['ord']==shift['ord']][0]
          cpu['users'] = []
        else:
          cpu['user'] = cpu['users'].pop(0)
      if shift is not None:
        data['shift_name'] = shift['name']
        data['shift'] = shift['ord']
        data['shift_count'] = 1

      data['subsubmenu'] = [
        {'title': s['name'], 'path': 'computers/%s' % objects.strip(s['name'])}
        for s in objects.listShifts()]

      web.outputPage(hypertext.frame('computers', data))
    elif path[0] == 'users':
      web.outputPage(hypertext.frame('users', data))
    elif path[0] == 'queue':
      web.outputPage(hypertext.frame('queue', data))
    elif path[0] == 'floorplan':
      html = '{{floorplan}}'

      if usr_lvl >= 100:
        hypertext.GLOBALS['scripts'].append('svg_draw.js')

      if len(path) > 1:
        shift = objects.getShift(path[1])
        html = '{{floorplan:%s}}' % (objects.strip(shift['name']),)

      data['subsubmenu'] = [
        {'title': s['name'], 'path': 'floorplan/%s' % objects.strip(s['name'])}
        for s in objects.listShifts()]

      web.outputPage(hypertext.frame(html, data, 'imgframe'))

  if usr_lvl >= 100:
    if path[0] == 'assign':
      if len(path) == 3:
        usr = objects.getPerson(path[1])
        if usr is None: web.redirect('users', 3, 'NO_USER')
        rc = objects.assignComputer(*path[1:])
        if len(rc) == 2: message = lang['MSG_ASSIGN_COMPUTER'] % rc
        elif len(rc) == 1: message = lang['MSG_UNASSIGN_COMPUTER'] % rc
        else: web.redirect('user/%d' % usr['pid'], 3, 'ERR_ASSIGN')
        log(2, message)
        objects.saveData()
        web.redirect('user/%d' % usr['pid'], 1, message)
      elif len(path) == 2:
        usr = objects.getPerson(path[1])
        if usr is None: web.redirect('users', 3, 'ERR_NO_PERSON')
        dt = { 'user': usr, 'computers': objects.listVacant(usr['shift_id']) }
        web.outputPage(hypertext.frame(hypertext.mustache(
          hypertext.layout('assign'), dt)))
    elif path[0] == 'delete' and len(path) == 3 \
        and path[1] in ('computer', 'user', 'shift', 'coach') \
        and objects.REGEX_INTEGER.match(path[2]):
      if path[1] == 'user': err = objects.deletePerson(int(path[2]))
      elif path[1] == 'computer': err = objects.deleteComputer(int(path[2]))
      elif path[1] == 'coach': err = objects.deleteCoach(int(path[2]))
      elif path[1] == 'shift': err = objects.deleteShift(int(path[2]))
      else: err = 'ERR_UNKNOWN_TYPE'

      if err is None:
        objects.saveData()
        if path[1] == 'user': web.redirect('users', 1, 'MSG_DELETE')
        elif path[1] == 'computer': web.redirect('computers', 1, 'MSG_DELETE')
        elif path[1] in ('shift', 'coach'):
          web.redirect('config', 1, 'MSG_DELETE')
        else: web.redirect('', 1, 'MSG_DELETE')
      else:
        log(1, 'Could not delete unit: %s %s' % (path[1], path[2]))
        if path[1] == 'user': web.redirect('users', 3, err)
        elif path[1] == 'computer': web.redirect('computers', 3, err)
        elif path[1] in ('shift', 'coach'): web.redirect('config', 3, err)
        else: web.redirect('', 3, err)
    elif path[0] == 'update' and len(path) == 4:
      cid, x, y = path[1], int(path[2]), int(path[3])
      objects.moveComputer(cid, x, y)
      objects.saveData()
      web.outputJSON({ 'success': True })
    elif path[0] == 'update' and len(path) == 3:
      sid, ud = int(path[1]), path[2]
      if ud == 'up': objects.moveShift(sid, False)
      elif ud == 'down': objects.moveShift(sid, True)
      else: raise ValueError('Unknown direction: %s' % ud)
      objects.saveData()
      web.outputJSON({ 'shifts': objects.listShifts(), 'success': True })
    elif path[0] == 'config':
      outputConfigPage()

  web.error404()

if __name__ == '__main__':
  if 'SERVER_ADDR' in os.environ: mainCGI()
  else: main()

