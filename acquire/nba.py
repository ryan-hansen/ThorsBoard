import re

from acquire.tagprocessor import TagProcessor

class TeamData(TagProcessor):

    def __init__(self, sport_code):
        super(TeamData, self).__init__(sport_code)

    def get_data(self, attrs={}):
        league = None
        for link in self._get_tags('a', attrs):
            try:
                league = link.find_parent('li').find_parent('li').find_parent('li').next.text
                href = link['href']
                name = link.text.strip(';')
                if str(name) == 'Portland Trail Blazers':
                    teamname = ' '.join(name.split(' ')[:-2])
                    alt_name = ' '.join(name.split(' ')[-2:])
                else:
                    teamname = ' '.join(name.split(' ')[:-1])
                    alt_name = ' '.join(name.split(' ')[-1:])
                match = re.search(self.team_href, href)
                self.team_data.append(dict(code=match.group(1), name=teamname, alt_name=alt_name, url=None, league=league))
            except KeyError:
                continue