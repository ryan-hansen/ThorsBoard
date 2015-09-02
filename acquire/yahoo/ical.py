import logging
import os
import re

from time import sleep
from icalendar import Calendar
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q

from ThorsBoard.acquire.pagereader import PageReader
from ThorsBoard.web.models import Team, Game, Season

class ICal(object):

    def __init__(self):
        logfile = 'not_found.log'
        logging.basicConfig(filename=logfile, filemode='w', format='%(asctime)s %(message)s', level=logging.INFO)
        self.logger = logging.getLogger('ical')
        self.season_start = timezone.make_aware(datetime(2013, 8, 29), timezone.get_default_timezone())

    def schedule(self, team, season=None):
        sport = team.sport.abbrev
        games = Game.objects.filter((Q(team1__id=team.id) | Q(team2__id=team.id)), season__id=season.id)
        if len(games) > 13:
            print 'Season already set for {0}'.format(team.name)
            return False
        team_code = team.yahoo_code
        if not team_code or team_code == 'aaa':
            print 'No Yahoo code found for {0}'.format(team.name)
            return False
        nonalpha = re.compile('[^\w ]+')
        filename = re.sub(nonalpha, '', team.name.lower().replace(' ', '_'))
        ics_file = os.path.join('schedules', '{0}.ics').format(filename)
        try:
            # Get last modified timestamp for ICS file
            mtime = datetime.fromtimestamp(os.path.getmtime(ics_file))
        except WindowsError:
            # ICS file doesn't exist, so fake the timestamp to 30 days old so the file will be created
            mtime = datetime.now() - timedelta(days=30)
        if (datetime.now() - timedelta(hours=24)) > mtime:
            print 'Retrieving latest data from source...'
            sleep(5)
            ics_url = 'http://rivals.yahoo.com/{0}/teams/{1}/ical.ics'.format(sport, team_code)
            reader = PageReader(ics_url)
            f = open(ics_file, 'w')
            f.write(reader.data)
            f.close()
        f = open(ics_file, 'r')
        ical = Calendar.from_ical(f.read())
        f.close()

        for comp in ical.walk():
            opponent = None
            if comp.name == 'VEVENT':
                teams = comp.get('summary').split(' at ')
                if teams[0] == team.name or teams[0] == team.abbrev or teams[0] in team.aliases:
                    opponent = teams[1]
                    #home = False
                else:
                    opponent = teams[0]
                    #home = True
                opp = Team.find.by_aliases(opponent)
                if not opp:
                    msg = 'Team {0} Not Found'.format(opponent)
                    print msg
                    self.logger.info(msg)
                    continue
                game_date = comp.get('dtstart')
                gdate = game_date.dt - timedelta(hours=6)
                try:
                    game = Game.find.by_opp_and_season(team, opp, season)
                    print '{0} vs. {1} Already Recorded'.format(team.name, opp.name)
                    if game.date != gdate:
                        print '----- UPDATING START TO {0} -----'.format(gdate)
                        game.date = gdate
                        game.save()
                    continue
                except IndexError:
                    if gdate < self.season_start:
                        print 'Game is scheduled for {0}; current season starts {1}'.format(gdate.date(), season.start_date)
                        continue
                    game = Game()
                    game.season = season
                    game.team1 = team
                    game.team2 = opp
                    game.date = gdate
                    print 'Saving {0} vs. {1}'.format(team.name, opp.name)
                    game.save()

    def run(self, target='schedule'):
        for team in Team.objects.all():
            if team.sport.abbrev != 'ncaaf':
                continue
            print 'Retreiving "{0}" for {1}'.format(target, team.name)
            if target == 'schedule':
                season = Season.objects.filter(start_date__gte=self.season_start)[0]
                self.schedule(team, season=season)

if __name__ == '__main__':
    ical = ICal()
    ical.run()
