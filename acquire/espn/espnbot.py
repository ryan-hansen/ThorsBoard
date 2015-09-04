import json
import os
import urllib2

from acquire.pagereader import PageReader

url = 'http://sports.espn.go.com/ncf/bottomline/scores'
reader = PageReader(url, soup=False)

parts1 = reader.data.split('&')
kv = {}
for p in parts1:
    try:
        parts = p.split('=')
        if 'ncf_s_left' in parts[0]:
            kv[parts[0]] = urllib2.unquote(parts[1])
    except IndexError:
        pass

scoreboard = os.path.join(os.path.dirname(__file__), '{0}_week{1}_scores.html')
output = json.dumps(kv)
f = open('')
