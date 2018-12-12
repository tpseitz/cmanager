#!/usr/bin/env python3
# Encoding: UTF-8
import datetime, time, os
import database, sykeit, web

log = database.log

def main():
  conf = sykeit.init()

  max_mtime = time.time() - web.COOKIE_AGE
  for fn in os.listdir(web.SESSION_DIRECTORY):
    ffn = os.path.join(web.SESSION_DIRECTORY, fn)
    mtime = os.stat(ffn).st_mtime
    age = mtime - max_mtime
    tt = datetime.datetime.fromtimestamp(mtime).strftime(
      database.LOG_TIME_FORMAT)
    if age < 0:
      log(3, 'Deleting old session file %s (%s)' % (fn, tt.strip()))
      os.unlink(ffn)

if __name__ == '__main__':
  main()

