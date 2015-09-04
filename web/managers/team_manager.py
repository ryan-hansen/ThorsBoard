from django.db import models


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