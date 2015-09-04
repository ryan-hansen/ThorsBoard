import requests

from bs4 import BeautifulSoup


class PageReader(object):

    def __init__(self, uri, soup=True):
        if uri.startswith('http'):
            try:
                req = requests.get(uri, headers={'User-Agent': "Magic Browser"})
                data = req.text
            except Exception, e:
                raise
        else:
            f = open(uri, 'r')
            data = f.read()
            f.close()
        self.data = data
        if soup:
            self.soup = BeautifulSoup(self.data)