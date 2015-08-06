from django.db import models
from django.utils import timezone
from datetime import datetime, time

from ThorsBoard.web.managers import TeamManager, GameManager, SeasonManager

class Sport(models.Model):
    name = models.CharField(max_length=255)
    abbrev = models.CharField(max_length=32)
    url = models.CharField(max_length=255)
    image = models.CharField(max_length=255)

    class Meta:
        db_table = 'sport'
        ordering = ['name']

    def __unicode__(self):
        return u'{name}'.format(name=self.name)

class League(models.Model):
    sport = models.ForeignKey(Sport, related_name='leagues')
    name = models.CharField(max_length=255)
    abbrev = models.CharField(max_length=16)

    class Meta:
        db_table = 'league'
        ordering = ['name']

    def __unicode__(self):
        return u'{name}'.format(name=self.name)

class Team(models.Model):
    sport = models.ForeignKey(Sport, related_name='teams')
    league = models.ForeignKey(League, related_name='teams')
    name = models.CharField(max_length=255)
    abbrev = models.CharField(max_length=16)
    alt_name = models.CharField(max_length=32)
    yahoo_code = models.CharField(max_length=8)
    merch_url = models.CharField(max_length=255)
    logo_team_id = models.IntegerField()
    ap_rank = models.IntegerField()
    bcs_rank = models.IntegerField()
    espn_rank = models.IntegerField()
    url = models.CharField(max_length=255)
    primary_color = models.CharField(max_length=16)
    alt_color = models.CharField(max_length=16)
    _other_names = models.CharField(max_length=32, db_column='aliases')
    objects = models.Manager()
    find = TeamManager()

    class Meta:
        db_table = 'team'
        ordering = ['name']

    def __unicode__(self):
        return u'{name}'.format(name=self.name)

    @property
    def aliases(self):
        # return a list with extraneous whitespace stripped
        names = [n.strip() for n in self._other_names.split(',')]
        if len(names[0]) > 0:
            return names
        else:
            return []

class Season(models.Model):
    sport = models.ForeignKey(Sport, related_name='seasons')
    start_date = models.DateField()
    label = models.CharField(max_length=100)
    objects = models.Manager()
    find = SeasonManager()

    class Meta:
        db_table = 'season'
        ordering = ['label']

    def __unicode__(self):
        return u'{label}'.format(label=self.label)

    @property
    def begins(self):
        begins = datetime.combine(self.start_date, time())
        return timezone.make_aware(begins, timezone.get_default_timezone())

class Game(models.Model):
    season = models.ForeignKey(Season, related_name='games')
    team1 = models.ForeignKey(Team, related_name='team1_games')
    team2 = models.ForeignKey(Team, related_name='team2_games')
    team1_score = models.IntegerField()
    team2_score = models.IntegerField()
    date = models.DateTimeField()
    objects = models.Manager()
    find = GameManager()

    class Meta:
        db_table = 'game'
        ordering = ['date']

    def __unicode__(self):
        return u'{date}'.format(date=self.date)

class User(models.Model):
    email = models.CharField(max_length=255, unique=True)
    nickname = models.CharField(max_length=25, blank=True)
    avatar = models.CharField(max_length=50, blank=True)
    password = models.CharField(max_length=50, blank=True)
    is_active = models.IntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    class Meta:
        db_table = u'user'

    def __unicode__(self):
        return u'{nickname}'.format(nickname=self.nickname)

class Group(models.Model):
    owner = models.ForeignKey(User)
    team = models.ForeignKey(Team, null=True, blank=True)
    type = models.BigIntegerField(null=True, blank=True)
    level = models.BigIntegerField(null=True, blank=True)
    name = models.CharField(max_length=100, blank=True)
    blog_url = models.CharField(max_length=255, blank=True)
    rss_url = models.CharField(max_length=255, blank=True)
    password = models.CharField(max_length=255, blank=True)
    max_users = models.BigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True, auto_now=True)
    slug = models.CharField(max_length=25, unique=True, blank=True)
    class Meta:
        db_table = u'group'

    def __unicode__(self):
        return u'{name}'.format(name=self.name)

class UserGroup(models.Model):
    user = models.ForeignKey(User)
    group = models.ForeignKey(Group)
    class Meta:
        db_table = u'group_user'

class Comment(models.Model):
    user = models.ForeignKey(User)
    group = models.ForeignKey(Group)
    game = models.ForeignKey(Game)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children')
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    class Meta:
        db_table = u'comment'

class Guess(models.Model):
    user = models.ForeignKey(User)
    game = models.ForeignKey(Game)
    group = models.ForeignKey(Group)
    myteam_score = models.BigIntegerField(null=True, blank=True)
    opponent_score = models.BigIntegerField(null=True, blank=True)
    accuracy = models.DecimalField(null=True, max_digits=20, decimal_places=1, blank=True)
    tb_score = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    class Meta:
        db_table = u'guess'

class UserTeam(models.Model):
    user = models.ForeignKey(User)
    team = models.ForeignKey(Team)
    class Meta:
        db_table = u'user_team'