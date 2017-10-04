""" custom_storages.py """

from django.conf import settings
from storages.backends.s3boto import S3BotoStorage

class StaticStorage(S3BotoStorage):
    """ Assign AWS S3 as default static files storage """

    location = settings.STATICFILES_LOCATION

class MediaStorage(S3BotoStorage):
    """ Assign AWS S3 as default media files storage """

    location = settings.MEDIAFILES_LOCATION
