import os
import re

from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from django.db.models import Q

from acquire.pagereader import PageReader
from web.models import Team, Season

class ESPNSchedule(object):
    gt_ptn = re.compile(r'([0-9])+')
    season_start = datetime(2013, 8, 29)

    def run(self, sport):
        season = Season.objects.filter(start_date__gte=self.season_start)[0]
        season_year = season.start_date.year
        schedule = os.path.join(os.path.dirname(__file__), '{0}_{1}.html'.format(season_year, sport))
        try:
            # Get last modified timestamp for schedule file
            mtime = datetime.fromtimestamp(os.path.getmtime(schedule))
        except WindowsError:
            # Schedule file doesn't exist, so fake the timestamp to 30 days old so the file will be created
            mtime = datetime.now() - timedelta(days=30)
        if (datetime.now() - timedelta(hours=24)) > mtime:
            url = 'http://espn.go.com/college-football/story/_/id/8987062/espn-networks-2013-college-football-schedule'
            self.reader = PageReader(url)
            f = open(schedule, 'w')
            f.write(self.reader.data)
            f.close()
        f = open(schedule, 'r')
        data = f.read()
        f.close()
        soup = BeautifulSoup(data.decode('utf-8', 'ignore'))
        for row in soup.find_all('tbody'):
            game_date = row.find_next('td')
            teams = game_date.find_next('td')
            game_time = teams.find_next('td')
            gt = game_time.text
            if ':' not in gt:
                gt = re.sub(self.gt_ptn, r'\1:00', game_time.text)
            if gt == 'Noon':
                gt = '12:00 PM'
            network = game_time.find_next('td')
            datestr = '{0} {1}'.format(game_date.text, gt).replace('.', '').replace(',', '').replace('Sept', 'Sep')
            parts = datestr.split()
            parts[0] = parts[0][:3]
            parts.insert(3, str(season_year))
            datestr = ' '.join(parts)
            try:
                game_day = datetime.strptime(datestr, '%a %b %d %Y %I:%M %p')
            except ValueError, ex:
                print 'Skipping {0}: {1}'.format(teams.text, ex)
                continue
            opps = teams.contents[-1:][0].split(' at ')
            if len(opps) < 2:
                opps = opps[0].split('vs.')
            t1 = opps[0].strip()
            t2 = opps[1].strip()
            try:
                team1 = Team.objects.filter(Q(name=t1) | Q(alt_name=t1) | Q(abbrev=t1))[0]
            except:
                print 'Skipping {0}'.format(teams.text)
                continue
            try:
                team2 = Team.objects.filter(Q(name=t2) | Q(alt_name=t2) | Q(abbrev=t2))[0]
            except:
                print 'Skipping {0}'.format(teams.text)
                continue
            print '{0} vs {1}'.format(team1, team2)

if __name__ == '__main__':
    s = ESPNSchedule()
    s.run('ncaaf')