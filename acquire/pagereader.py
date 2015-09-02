import httplib2
import urllib2

from bs4 import BeautifulSoup


class PageReader(object):

    def __init__(self, uri, soup=True):
        if uri.startswith('http'):
            req = urllib2.Request(uri, headers={'User-Agent' : "Magic Browser"})
            try:
                con = urllib2.urlopen( req )
                code = con.getcode()
            except Exception, e:
                pass
            data = ''
            for line in con.read():
                data += line
            con.close()
        else:
            f = open(uri, 'r')
            data = f.read()
            f.close()
        self.data = data
        if soup:
            self.soup = BeautifulSoup(self.data)

    def _getContentLocation(self, url):
        h = httplib2.Http(disable_ssl_certificate_validation=True)
        h.follow_all_redirects = True
        resp = h.request(url, "GET")[0]
        contentLocation = resp['content-location']
        return contentLocation