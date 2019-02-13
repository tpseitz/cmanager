#!/usr/bin/env python3
# Encoding: UTF-8
import json, os
CONFIG_FILES = [
  '~/.config/computer_manager.json',
  '/etc/cmanager/config.json',
  '/etc/computer_manager.json',
  os.sep.join(os.path.realpath(__file__).split(os.sep)[:-2]) \
    + '/computer_manager.json']
DAY_COUNT = 5

COMPUTER_ID = {}

def convertComputers(ffn):
  global COMPUTER_ID

  with open(ffn, 'r') as f: data = json.loads(f.read())
  print('INSERT INTO computers (name, location_x, location_y) VALUES')
  rd = []
  for cpu in data:
    rd.append('("%s", %s, %s)'
      % tuple([cpu.get(k) or 'NULL' for k in ['name', 'x', 'y']]))
    COMPUTER_ID[cpu['cid']] = cpu['name']
  print('  ' + ',\n  '.join(rd) + ';')

def handleDays(days):
  days = set(days)
  dl = []
  for i in range(DAY_COUNT): dl.append(i in days and 'TRUE' or 'FALSE')
  return tuple(dl)

def selectShift(nm):
  if nm is None: return 'NULL'
  return '(SELECT sid FROM shifts WHERE name = "%s")' % nm

def selectComputer(nm):
  global COMPUTER_ID

  if nm is None: return 'NULL'
  return '(SELECT cid FROM computers WHERE name = "%s")' % COMPUTER_ID[nm]

def convertPeople(ffn):
  global _COMPUTER_ID

  with open(ffn, 'r') as f: data = json.loads(f.read())
#  print(', '.join(sorted(data[0].keys())))
  print('INSERT INTO persons (name, shift_id, '
    + ', '.join(['day_%d' % i for i in range(DAY_COUNT)])
    + ', computer_id) VALUES')
  rd = []
  for usr in data:
    dt = (usr['name'], selectShift(usr['shift_name']))
    dt = dt + handleDays(usr['days'])
    dt = dt + (selectComputer(usr['computer']),)
    rd.append(
      ('("%s", ' + ', '.join('%s' for i in range(2 + DAY_COUNT)) + ')') % dt)
  print('  ' + ',\n  '.join(rd) + ';')

def readConfig():
  cfn, ufn = None, None
  for ffn in CONFIG_FILES:
    ffn = os.path.expanduser(ffn)
    if os.path.isfile(ffn):
      with open(ffn, 'r') as f: conf = json.loads(f.read())
      cfn = os.path.join(conf['data_directory'], 'computers.json')
      ufn = os.path.join(conf['data_directory'], 'users.json')
      return cfn, ufn

  return None, None

if __name__ == '__main__':
  cfn, ufn = readConfig()
  if cfn and ufn:
    convertComputers(cfn)
    convertPeople(ufn)

