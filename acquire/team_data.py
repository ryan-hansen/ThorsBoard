from time import sleep

from ThorsBoard.web.models import Sport, Team, League
from ThorsBoard.acquire.wiki.wikipedia import Wikipedia
from ThorsBoard.acquire.team_wikipedia import TEAMS

def _get_wikipedia_data(sport, team):
    wikidata = {}
    if sport not in ['nba', 'nfl']:
        page = TEAMS[team.name]
    else:
        page = '{0}_{1}'.format(team.name.replace(' ', '_'), team.alt_name.replace(' ', '_'))
        page.replace('76Ers', '76ers') # fix 76ers page
    wiki_url = "https://en.wikipedia.org/wiki/{0}".format(page)
    wiki = Wikipedia(wiki_url)
    arena = wiki.arena
    if sport not in ['nba', 'nfl']:
        team.alt_name = wiki.nickname
    colors = wiki.colors
    wikidata['arena'] = arena
    wikidata['primary'] = colors['primary']
    wikidata['alt'] = colors['alt']
    return wikidata

def get_team_data(sport_code):
    imp = 'thorsboard.acquire.{0}'.format(sport_code)
    module = __import__(imp, globals(), locals(), ['TeamData'], -1)
    teamdata = module.TeamData(sport_code)
    sport = Sport.objects.filter(abbrev=sport_code)[0]
    if not sport:
        return

    for td in teamdata.team_data:
        teamname = str(td['name'])
        defaults = {
            'sport': sport,
        }
        league, created = League.objects.get_or_create(name=str(td['league']), defaults=defaults)
        try:
            team = Team.objects.filter(name=teamname, league=league)[0]
            team.yahoo_code = td['code']
            print 'Saving code for {0} ({1})'.format(team.name, team.yahoo_code)
        except IndexError:
            defaults = {
                'sport': sport,
                'yahoo_code': str(td['code']),
                'url': str(td['url']),
                'alt_name': td.get('alt_name', None),
                'league': league,
            }
            team, created = Team.objects.get_or_create(name=teamname, defaults=defaults)
            if created:
                print 'Created {0}'.format(team.name)
        if not team.primary_color:
            sleep(5)
            wikidata = _get_wikipedia_data(sport_code, team)
            team.primary_color = wikidata['primary']
            team.alt_color = wikidata['alt']
        if not team.aliases and 'St.' in team.name:
            team._other_names = team.name.replace('St.', 'State')
        if not team.aliases and 'Intl.' in team.name:
            team._other_names = team.name.replace('Intl.', 'International')
        print 'Finished {0}'.format(team.name)
        team.save()

if __name__ == '__main__':
    get_team_data('ncaaf')
    #get_team_data('nba')