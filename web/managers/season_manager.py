from datetime import datetime
from django.db import models


class SeasonManager(models.Manager):

    def current(self):
        return self.get_queryset().filter(start_date__lt=datetime.utcnow()).order_by('-start_date')[0]