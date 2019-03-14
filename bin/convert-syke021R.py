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
  print('INSERT INTO computers (name, x, y) VALUES')
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

