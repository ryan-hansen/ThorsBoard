import json
import os

from ThorsBoard.web.models import Team, League

class BuildFixture(object):

    def run(self, league):
        teams = list()
        leagues = League.objects.filter(sport__abbrev=league)
        for l in leagues:
            conf = dict()
            conf[l.name] = list()
            for team in Team.objects.filter(league__id=l.id):
                team = {
                    'name': team.name,
                    'abbrev': team.abbrev,
                    'alt_name': team.alt_name,
                    'color': team.primary_color,
                    'alt_color': team.alt_color,
                    'yahoo_code': team.yahoo_code,
                }
                conf[l.name].append(team)
            teams.append(conf)
        fp = open(os.path.join(os.path.dirname(__file__), '{0}_teams.json'.format(league)), 'w')
        fp.write(json.dumps(teams, indent=4))
        fp.close()
        print 'Done'

if __name__ == '__main__':
    f = BuildFixture()
    f.run('nba')