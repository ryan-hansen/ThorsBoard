import re

from bs4 import BeautifulSoup

class TagProcessor(object):

    def __init__(self, sport_code):
        self.datasource = 'yahoo/{code}_teams.html'.format(code=sport_code)
        f = open(self.datasource, 'r')
        html = f.read()
        f.close()
        self.process(html)
        ptn = '/{code}/teams/([a-z]+)'.format(code=sport_code)
        self.team_href = re.compile(ptn)
        code_attrs = { 'href' : self.team_href }
        self.get_data(code_attrs)

    def process(self, html):
        self.soup = BeautifulSoup(html)
        self.team_data = []

    def _get_tags(self, tag, attrs):
        return self.soup.find_all(tag, attrs)

    def get_data(self, attrs={}):
        """
        Parse the Yahoo team listing HTML to get team names and conferences.
        Default functionality (below) applies only for NCAA Football; all other leagues must override this function in
        their own league-specific subclass (e.g. nba.py).
        """
        league = None
        for link in self._get_tags('a', attrs):
            try:
                league = link.find_previous('span', { 'class': 'yspdetailttl' }).text
                href = link['href']
                name = link.text.strip(';')
                try:
                    cls = link.nextSibling.nextSibling.get('class')
                    if cls and cls != 'yspdetailttl':
                        site = link.nextSibling.nextSibling.text
                    else:
                        site = None
                except:
                    pass
                match = re.match(self.team_href, href)
                self.team_data.append(dict(code=match.group(1), name=name, url=site, league=league))
            except KeyError:
                continue