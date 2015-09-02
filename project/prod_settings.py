from ThorsBoard.project.settings import *

DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',   # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'thorsboard',                      # Or path to database file if using sqlite3.
        'USER': 'thorsboarddb',                       # Not used with sqlite3.
        'PASSWORD': 'I@mB0ard!',                 # Not used with sqlite3.
        'HOST': '',                             # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                             # Set to empty string for default. Not used with sqlite3.
    }
}