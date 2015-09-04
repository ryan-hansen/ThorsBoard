import argparse
import django
import json
import logging
import os
import re

from bs4 import BeautifulSoup
from django.utils import timezone
from datetime import datetime, timedelta
from dateutil import parser

from acquire.logs import LOG_PATH
from acquire.pagereader import PageReader
from web.models import Team, Game, Season

django.setup()


class ScoreBot(object):

    def __init__(self):
        logfile = os.path.join(LOG_PATH, 'scorebot.log')
        logging.basicConfig(filename=logfile, filemode='w', format='%(asctime)s %(message)s', level=logging.INFO)
        parser = argparse.ArgumentParser()
        parser.add_argument('-w', '--week',
                            help='Set the week of the season to target')
        parser.add_argument('-d', '--debug',
                            help='Turn on debug output',
                            action='store_true')
        parser.add_argument('-u', '--update',
                            help='Update data from live source',
                            action='store_true')
        parser.add_argument('-s', '--sport',
                            help='The code of the sport to target (e.g. NCAA Football = ncaaf)',
                            default='ncaaf')
        self.args = parser.parse_args()
        self.logger = logging.getLogger('ScoreBot')
        self.reader = None
        self.week = None
        self.current_season = Season.find.current()

    def load_games(self):
        if not self.args.week:
            for w in xrange(1, 15):
                self.load_week(w)
        else:
            week = self.args.week
            if week in ['current', 'next']:
                week = self.get_week(week)
            self.load_week(week)

    def load_week(self, week=None):
        self.log('Loading week {0}'.format(week))
        try:
            self.get_data(week)
        except Exception, e:
            self.log('Trying again to retreive data...')
            self.get_data(week)
        data = json.loads(self.reader.data)
        for g, html in data['games'].iteritems():
            date_str = re.sub('[^0-9]*', '', g)[:-4]
            game_date = datetime.strptime('{0}1000'.format(date_str), '%Y%m%d%H%M')
            game_date = timezone.make_aware(game_date - timedelta(hours=2), timezone.UTC())
            g = BeautifulSoup(html, 'html.parser')
            try:
                teams = self.get_teams(g)
            except Exception, e:
                print e
                continue
            home = [el for el in teams if el['home'] is True][0]
            away = [el for el in teams if el['home'] is False][0]
            game = Game.find.by_opp_and_season(home['team'], away['team'], self.current_season)
            if game and (game.home_score and game.away_score):
                self.log('Score already set: {0}: {1} - {2}: {3}'.format(
                    game.home.name,
                    game.home_score,
                    game.away.name,
                    game.away_score)
                )
                continue
            if not game:
                self.log('Could not find a game between {0} and {1}...creating'.format(
                    home['team'],
                    away['team']), 'warning')
                game = Game()
                game.season = self.current_season
                game.date = game_date
                game.home = home['team']
                game.away = away['team']
                game.save()
            self.set_time(g, game)

    def set_time(self, game_tag, game):
        try:
            time = game_tag.find('span', {'class': 'time'}).text
            if time == 'TBA':
                return
            try:
                edate = parser.parse(time)
            except ValueError:
                if ' ' in time:
                    parts = time.split(' ')
                    time = parts[0].split(':')
                    hour = int(time[0])
                    minute = int(time[1])
                    meridian = parts[1]
                    start_time = '{0:02d}:{1:02d} {2}'.format(hour, minute, meridian)
                    datestr = '{0} {1}'.format(datetime.strftime(game.date, '%Y-%m-%d'), start_time)
                    edate = datetime.strptime(datestr, '%Y-%m-%d %I:%M %p')
            gdate = timezone.make_aware(edate - timedelta(hours=2), timezone.UTC())
            if gdate != game.date:
                self.log('Updating Start Time for {0} vs. {1}'.format(game.home.name, game.away.name))
                game.date = gdate
                game.save()
            return gdate
        except AttributeError:
            self.set_score(game_tag, game)

    def set_score(self, game_tag, game):
        away_attrs = {'class': re.compile('away.*')}
        a = game_tag.find('span', away_attrs).text
        if not a:
            return
        home_attrs = {'class': re.compile('home.*')}
        h = game_tag.find('span', home_attrs).text
        game.home_score = h
        game.away_score = a
        self.log('Setting Score: {0}: {1} - {2}: {3}'.format(
            game.home.name,
            game.home_score,
            game.away.name,
            game.away_score
        ))
        game.save()

    def get_data(self, week):
        scoreboard = os.path.join(os.path.dirname(__file__), '{0}_week{1}_scores.html'.format(
            self.current_season.begins.year,
            week
            )
        )
        if not os.path.exists(scoreboard) or self.args.update:
            msg = 'Retrieving latest data from source...'
            self.log(msg)
            live_url = 'http://sports.yahoo.com/__xhr/sports/scoreboard/gs/?lid={0}&week={1}&conf=all'.format(
                self.args.sport, week )
            reader = PageReader(live_url, soup=False)
            try:
                json.loads(reader.data)
                f = open(scoreboard, 'w')
                f.write(reader.data)
                f.close()
            except ValueError, ex:
                self.log('Something broke: {0}'.format(ex), 'error')
                raise
        # Open and read from the local file in all cases
        local_url = scoreboard
        self.reader = PageReader(local_url, soup=False)

    def get_teams(self, game):
        teams = list()
        team_tags = game.find_all('span', {'class': 'team'})
        ptn = '\((?P<rank>[0-9]*)\)'
        re.compile(ptn)
        for t in team_tags:
            team = dict(team=None, home=False)
            rank = None
            team_name = t.text.replace(';', '')
            matched = re.search(ptn, team_name)
            if matched:
                rank = matched.group('rank')
                team_name = re.sub(ptn, '', team_name)
            home = True if t.find_previous('td').attrs.get('class')[0] == 'home' else False
            t = Team.find.by_aliases(team_name.strip())
            if t:
                t.ap_rank = rank
                t.save()
            else:
                raise Exception('No Team Found: {0}'.format(team_name))
            team['team'] = t
            team['home'] = home
            teams.append(team)
        return teams

    def get_week(self, week='current'):
        now = timezone.make_aware(datetime.now(), timezone.get_default_timezone())
        delta = now - self.current_season.begins
        w = int(round(delta.total_seconds() / 60 / 60 / 24 / 7))
        if week == 'next':
            w += 1
        return w

    def log(self, msg, level='info'):
        if self.args.debug:
            print msg
        logger = getattr(self.logger, level)
        logger(msg)


if __name__ == '__main__':
    s = ScoreBot()
    s.load_games()