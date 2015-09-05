import itertools

from django.db import models

from project.const import TEAM_ALTERNATIVES


class TeamManager(models.Manager):
    def by_aliases(self, team_name):
        try:
            matches = self.get_queryset().filter(
                models.Q(name=team_name) |
                models.Q(abbrev=team_name) |
                models.Q(_other_names__contains=team_name)
            )
            for team in matches:
                if team_name == team.name or team_name == team.abbrev or team_name in team.aliases:
                    return team
            return None
        except IndexError:
            return None

    def alternatives(self, alt_name):
        alt_name = alt_name.replace('.', '').strip()
        parts = alt_name.split(' ')
        total_possible = list()

        for p in parts:
            try:
                total_possible.append(TEAM_ALTERNATIVES[p])
            except KeyError:
                total_possible.append([p])

        for perm in itertools.product(*total_possible):
            team_name = ' '.join(perm)
            print '---- TRYING {0} ----'.format(team_name)
            try:
                team = self.get_queryset().get(name=team_name)
                print '---- FOUND {0} ----'.format(team.name)
                print '---- ADDING {0} AS ALIAS ----'.format(alt_name)
                team.aliases = [alt_name]
                team.save()
                return team
            except self.model.DoesNotExist:
                continue

        raise self.model.DoesNotExist