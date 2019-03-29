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

import collections, datetime, json, re, os
LAYOUT_DIRECTORY = '~/layout'
FORMS, FUNCTIONS = {}, {}
GLOBALS = { 'menu': None, 'submenu': None, 'stylesheets': [],
  'scripts': [], 'js_init': '' }
PATH_ADMIN, PATH_COMPUTERS = '/admin', '/konehallinta'
FORMAT_DATE = '%Y-%m-%d'
JQUERY_UI_LOCATION = None

HTML_CELL_FREE = None
HTML_CELL_RESERVED = None

DATE_CONVERT = { '%y': 'y', '%Y': 'yy', '%m': 'mm', '%b': 'M',
  '%B': 'MM', '%d': 'dd', '%a': 'D', '%A': 'DD' }

REGEX_FORM_VARIABLE = re.compile(r'{[a-z_]+}')
REGEX_MUSTACHE_BLOCK = re.compile(
  r'\{\{\#(\$\d+|[A-Za-z_\.]+)(=[A-Za-z\d\._]+)?\}\}')
REGEX_MUSTACHE_VARIABLE = re.compile(
  r'\{\{(\&?)(\$\d+|[A-Za-z\._]+)(\:[A-Za-z\d_,]+)?\}\}')
REGEX_MUSTACHE_BLOCK_BARE = re.compile(r'\{\{[^\{\}]+\}\}')

def log(lvl, msg): pass

def datetimeFormatToJS(frm):
  for s, r in DATE_CONVERT.items(): frm = frm.replace(s, r)
  return frm

def init(lang_code):
  global GLOBALS, FORMS

  fdn = os.path.split(os.path.realpath(__file__))[0]
  ffn = os.path.join(fdn, 'lang-%s.json' % lang_code)
  with open(ffn, 'r') as f: lang = json.loads(f.read())
  ffn = os.path.join(fdn, 'forms.json')
  with open(ffn, 'r') as f: FORMS = json.loads(f.read())
  GLOBALS['lang'] = lang

  if JQUERY_UI_LOCATION:
    GLOBALS['stylesheets'].append('%s/jquery-ui.min.css' \
      % (JQUERY_UI_LOCATION,))
    GLOBALS['scripts'].append('%s/external/jquery/jquery.js' \
      % (JQUERY_UI_LOCATION,))
    GLOBALS['scripts'].append('%s/jquery-ui.min.js' % (JQUERY_UI_LOCATION,))
    GLOBALS['scripts'].append('%s/master/ui/i18n/datepicker-%s.js' \
      % (JQUERY_UI_LOCATION, lang_code))
    GLOBALS['js_init'] = GLOBALS['js_init'] \
      + '$.datepicker.setDefaults($.datepicker.regional["fi"]);\n' \
      + '$.datepicker.setDefaults({ dateFormat: "%s" });' \
        % (datetimeFormatToJS(FORMAT_DATE),)

  return lang

def link(path, text):
  if path and path[0] == '/': path = path[1:]
  return '<a href="%s/%s">%s</a>' % (GLOBALS['script'], path, text)

DATEPICKER_ELEMENT = \
  '  <script>$(function() { $("#%s").datepicker(); });</script>\n'
def form(name, data={}, formdata=None, redirect=None, target=None):
  global JQUERY_UI_LOCATION

  if name in FORMS: formdata = FORMS[name]
  elif formdata is None: return 'form(%s)' % (name,)
  title, button, redirect = formdata[0]
#  if not title: title = name
  if not target: target = 'form'

  html = '<form id="%s" action="{{script}}/%s"' % (name, target) \
    + ' method="post" enctype="multipart/form-data">\n'
  if title: html += '  <p>%s</p>\n' % (title,)
  html += '  <input type="hidden" name="_form" value="%s">\n' % (name,)
  src = os.environ.get('REQUEST_URI')
  if src: html += '  <input type="hidden" name="_source" value="%s">\n'% (src,)

  for iid, tp, nm, vls in formdata[1:]:
    if isinstance(vls, str) and REGEX_FORM_VARIABLE.match(vls):
      vls = GLOBALS.get(vls[1:-1], [])

    if   tp == 'static':
      html += '  <p>%s: %s</p>\n' % (nm, vls[1])
      if vls: html += '  <input type="hidden" name="%s" value="%s">\n' \
        % (iid, vls[0])
    elif tp == 'text':
      html += '  <p>%s<input type="text" name="%s" value=""></p>\n' % (nm, iid)
    elif tp == 'date':
      dt = datetime.date.today()
      if vls and isinstance(vls, int): dt += datetime.timedelta(days=vls)
      html += '  <p>%s<input type="text" name="%s" id="%s" value="%s"></p>\n' \
        % (nm, iid, iid, dt.strftime(FORMAT_DATE))
      if JQUERY_UI_LOCATION:
        html += DATEPICKER_ELEMENT % (iid,)
    elif tp in ('select', 'select0'):
      iter(vls) # Test that vls is of iterable type
      html += '  <p>%s\n' % (nm,)
      html += '  <select name="%s" required="true">\n' % iid
      if tp == 'select0': html += '    <option value="null">-</option>\n'
      for i, n in vls:
        html += '    <option value="%s">%s</option>\n' % (i, n)
      html += '  </select></p>\n'
    elif tp == 'checklist':
      html += '  <p class="checklist"><strong>%s:</strong>\n' % (nm,)
      for i, n in vls:
        html += '  <input type="checkbox" name="%s" value="%s">%s\n' \
          % (iid, i, n)
      html += '  </p>\n'
    elif tp == 'password':
      html += '  <p>%s<input type="password" name="%s" value=""></p>\n' \
        % (nm, iid)

  html += '  <input type="hidden" name="_next" value="%s">\n' % (redirect,)
  html += '  <input id="send" class="button" type="submit" value="%s"><br>\n' \
    % (button,)
  html += '</form>\n'

  return html

FUNCTIONS['form'] = form

def layout(name):
  ffn = os.path.join(os.path.expanduser(LAYOUT_DIRECTORY), '%s.html' % (name,))
  if not os.path.isfile(ffn):
    ffn = os.path.join(os.path.expanduser(LAYOUT_DIRECTORY), '%s.svg' % (name,))
  if not os.path.isfile(ffn): return name
  with open(ffn, 'r') as f: html = f.read()
  return html

REGEX_LAYOUT_NAME = re.compile(r'^[a-z\d_]+$')
def frame(html, data={}, frame='frame'):
  if REGEX_LAYOUT_NAME.match(html): html = layout(html)
  start, end = layout(frame).split('{{content}}')
  return mustache(start + html + end, data)

def _getValue(key, default, *values):
  global GLOBALS, FUNCTIONS

  if key in ('_', '.'): return default
  if key.startswith('lang.'): return lang.get(key[5:], key[5:])
  if key in FUNCTIONS: return FUNCTIONS[key]

  for val in values + (FUNCTIONS, GLOBALS):
    found = False
    for k in key.split('.'):
      if k in val:
        val = val[k]
        found = True
      else:
        found = False
        break
    if found: break

  if not found: return '[%s]' % key

  return val

MAX_ITERATIONS, MAX_PAGE_SIZE = 25, 1048576
MAX_BLOCK_LOOPS, MAX_VARIABLE_LOOPS = 15, 150
def mustache(html, data={}, default=None, *outside):
  global GLOBALS

  # Check for max iterations
  if len(outside) > MAX_ITERATIONS: log(0, 'Stack overflow')
  # Check for too larde html page
  if len(html) > MAX_PAGE_SIZE: log(0, 'Page is too large')

  if REGEX_LAYOUT_NAME.match(html): html = layout(html)

  count = 0
  while count < MAX_BLOCK_LOOPS:
    count += 1
    mt = REGEX_MUSTACHE_BLOCK.search(html)
    if mt is None: break

    tag, key, compare = mt.group(0), mt.group(1), mt.group(2)
    i, l = html.find('{{/%s}}' % key), 5 + len(key)
    if i < 0: log(0, 'Layout error: No end tag for %s' % (tag,))
    start, blk, nblk, end = html[:mt.start()], html[mt.end():i], '', html[i+l:]
    if '{{^%s}}' % key in blk: blk, nblk = blk.split('{{^%s}}' % key, 1)

    val = _getValue(key, default, data, *outside)

    if compare:
      cp = data
      for k in compare[1:].split('.'):
        tmp = collections.ChainMap(cp, *outside, GLOBALS, FUNCTIONS)
        cp = tmp.get(k)
        if val is None: break
      val = val == cp

    if not val or val == '[%s]' % key:
      ht = mustache(nblk, data, *outside)
    elif isinstance(val, (tuple, list, set)):
      ht = ''
      for vv in val:
        dt = data
        if isinstance(vv, dict): dt = vv
        elif isinstance(vv, (tuple, list)):
          dt = { '$%d' % (i + 1): n for i, n in enumerate(vv)}
        ht += mustache(blk, dt, vv, data, *outside)
    elif callable(val):
      argv = mustache(blk, data, *outside).split(',')
      try: #XXX
        ht = val(*argv)
      except TypeError as te: raise TypeError('%r' % (argv,)) #XXX
    else:
      dt = data
      if isinstance(val, dict): dt = val
      ht = mustache(blk, dt, val, data, *outside)
    html = start + ht + end

  if count >= MAX_BLOCK_LOOPS:
    raise Exception('Maximum loop count reached: %d' % count)

  count = 0
  while count < MAX_VARIABLE_LOOPS:
    count += 1
    mt = REGEX_MUSTACHE_VARIABLE.search(html)
    if mt is None: break

    tp, key, arg = mt.groups()
    tag, rep = mt.group(0), '[no data]'

    val = _getValue(key, default, data, *outside)

    if callable(val):
      argv = tuple()
      if arg and arg[0] == ':': argv = arg[1:].split(',')
      rep = val(*argv)
    elif isinstance(val, (tuple, list, set)):
      rep = ', '.join(map(str, val))
    else:
      rep = str(val)

    html = html.replace(tag, rep)

  if count >= MAX_VARIABLE_LOOPS:
    raise Exception('Maximum loop count reached: %d' % count)

  return html

