from django.db import models

from datetime import datetime


class SeasonManager(models.Manager):

    def current(self):
        return self.get_query_set().filter(start_date__lt=datetime.utcnow()).order_by('-start_date')[0]