import json
import logging
import os
import re
import sys

from django.utils import timezone
from datetime import datetime, timedelta

from ThorsBoard.acquire.logs import LOG_PATH
from ThorsBoard.acquire.pagereader import PageReader
from ThorsBoard.web.models import Team, Game, Season

class ScoreBot(object):

    def __init__(self, sport='ncaaf', week=None, update=False, debug=False):
        logfile = os.path.join(LOG_PATH, 'scorebot.log')
        logging.basicConfig(filename=logfile, filemode='w', format='%(asctime)s %(message)s', level=logging.INFO)
        self.logger = logging.getLogger('ScoreBot')
        self.current_season = Season.find.current()
        self.debug = debug
        if not week:
            week = self.get_week()
        if week == 'next':
            week = self.get_week(next=True)
        self.week = week
        scoreboard = os.path.join(os.path.dirname(__file__), '{0}_week{1}_scores.html'.format(self.current_season.begins.year, week))
        if not os.path.exists(scoreboard) or update:
            msg = 'Retrieving latest data from source...'
            print msg
            live_url = 'http://sports.yahoo.com/__xhr/sports/scoreboard/gs/?lid={0}&week={1}&conf=all'.format(sport, week)
            reader = PageReader(live_url)
            data = ''
            try:
                json_data = json.loads(reader.data)
            except ValueError, ex:
                self.log('Something broke: {0}'.format(ex), 'error')
                return
            for game,html in json_data['games'].iteritems():
                try:
                    data += '{0}'.format(html)
                except UnicodeEncodeError:
                    continue
            if not data.startswith('<table>'):
                data = '<table>{0}</table>'.format(data)
            f = open(scoreboard, 'w')
            f.write(data)
            f.close()
        # Open and read from the local file in all cases
        local_url = scoreboard
        self.reader = PageReader(local_url)

    def update(self):
        self.log('### UPDATING SCHEDULES AND SCORES FOR WEEK {0} ###'.format(self.week))
        self.get_games('scores')
        self.get_games('schedules')

    def get_games(self, target='scores'):
        if target == 'scores':
            attrs = {'class': 'game link'}
        else:
            attrs = {'class': 'game pre link'}
        games = self.reader.soup.find_all('tr', attrs)
        for g in games:
            home = self.get_team(g, target=target)
            if not home:
                continue
            away = self.get_team(g, home=False, target=target)
            if not away:
                continue
            game = Game.find.byOpponentsAndSeason(home, away, self.current_season)
            if game and (game.team1_score and game.team2_score):
                self.log('Score already set: {0}: {1} - {2}: {3}'.format(
                    game.team1.name,
                    game.team1_score,
                    game.team2.name,
                    game.team2_score)
                )
                continue
            if not game:
                self.log('Could not find a game between {0} and {1}...creating...'.format(home, away), 'warning')
                game = Game()
                game.season = self.current_season
                game.date = timezone.make_aware(datetime.utcnow(), timezone.get_default_timezone())
                game.team1 = home
                game.team2 = away
                game.save()
            if target == 'scores':
                self.set_score(g, game, home)
            else:
                self.set_schedule(g, game)

    def set_schedule(self, game_tag, game):
        away_tag = game_tag.find_next('td', {'class': 'away'})
        time = away_tag.find_next('span', {'class': 'state'}).text
        parts = time.split(' ')
        time = parts[0].split(':')
        hour = int(time[0])
        minute = int(time[1])
        meridian = parts[1]
        tz = parts[2]
        start_time = '{0:02d}:{1:02d} {2}'.format(hour, minute, meridian)
        try:
            date = game_tag.find_previous('tr', {'class':'date'}).text
            parts = date.split(' ')
            dow = parts[0].strip(',')
            mon = parts[1]
            day = int(parts[2])
        except AttributeError:
            dow = datetime.strftime(game.date, '%A')
            mon = datetime.strftime(game.date, '%B')
            day = int(datetime.strftime(game.date, '%d'))
        game_date = '{0} {1} {2:02d} {3}'.format(dow, mon, day, self.current_season.begins.year)
        datestr = '{0} {1}'.format(game_date, start_time)
        edate = datetime.strptime(datestr, '%A %B %d %Y %I:%M %p')
        gdate = timezone.make_aware(edate - timedelta(hours=2), timezone.UTC())
        if gdate != game.date:
            self.log('Updating Start Time for {0} vs. {1}'.format(game.team1.name, game.team2.name))
            game.date = gdate
            game.save()
        return gdate

    def get_team(self, game, home=True, target='scores'):
        if home:
            field = 'home'
        else:
            field = 'away'
        attrs = {'class': field}
        team_tag = game.find_next('td', attrs)
        try:
            details = team_tag.find_next('span', {'class': 'team'}).text
        except AttributeError:
            return None
        if 'Final' not in details and target == 'scores':
            return None
        team_name = team_tag.find_next('em').text
        team = Team.find.byAliases(team_name)
        if not team:
            self.log('Cannot find team {0}'.format(team_name), 'warning')
            return
        return team

    def set_score(self, game_tag, game, home):
        score_tag = game_tag.find_next('td', {'class': 'score'})
        away_attrs = {'class': re.compile('away.*')}
        a = score_tag.find_next('span', away_attrs).text
        if not a:
            return
        home_attrs = {'class': re.compile('home.*')}
        h = score_tag.find_next('span', home_attrs).text
        if game.team1_id == home.id:
            game.team1_score = h
            game.team2_score = a
        else:
            game.team1_score = a
            game.team2_score = h
        self.log('Setting Score: {0}: {1} - {2}: {3}'.format(
            game.team1.name,
            game.team1_score,
            game.team2.name,
            game.team2_score
        ))
        game.save()

    def get_week(self, next=False):
        now = timezone.make_aware(datetime.now(), timezone.get_default_timezone())
        delta = now - self.current_season.begins
        week = round(delta.total_seconds() / 60 / 60 / 24 / 7)
        return int(week + 1)

    def log(self, msg, level='info'):
        if self.debug:
            print msg
        logger = getattr(self.logger, level)
        logger(msg)


if __name__ == '__main__':
    try:
        week = sys.argv[1]
        if week == 'current':
            week = None
    except IndexError:
        week = None
    try:
        update = sys.argv[2]
        if update == 'false':
            update = False
    except IndexError:
        update = False
    try:
        debug = sys.argv[3]
    except IndexError:
        debug = False
    s = ScoreBot(week=week, update=update, debug=debug)
    s.update()