""" teamiota/models.py """

import os
import shutil
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage as storage
from django.core.urlresolvers import reverse
from django.dispatch.dispatcher import receiver

from iotaProject import settings

from wand.image import Image

class Location(models.Model):
    """ Normal User Location """

    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Department(models.Model):
    """ Normal User Department """

    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

def signature_path(instance, filename):
    """ Path to save signature image based on id """

    img_path = 'signatures/{0}/sig.png'.\
              format(str(instance.user.id))
    os_path = os.path.join(settings.MEDIA_ROOT, img_path)
    if os.path.exists(os_path):
        os.remove(os_path)
    return img_path

def validate_image(value):
    """ Check extension on uploaded image """

    valid_extensions = ['png', 'jpg', 'jpeg']
    valid = False
    for ending in valid_extensions:
        if value.name.endswith(ending):
            valid = True
    if value.name == '':
        valid = True
    if not valid:
        raise ValidationError(
            u'File type must be one of the following: [' + \
            ', '.join(valid_extensions) + \
            ']. Your file: ' + value.name)

class NormalUser(models.Model):
    """ Additional Profile information for a User """

    user = models.OneToOneField(User, unique=True, default=0, on_delete=models.CASCADE)
    nickname = models.CharField(null=True, blank=True, max_length=50)
    location = models.ForeignKey(Location, null=True, 
                                 on_delete=models.SET_NULL)
    department = models.ForeignKey(Department, null=True, 
                                   on_delete=models.SET_NULL)
    isAdmin = models.BooleanField(default=False)
    signatureImage = models.ImageField(
        upload_to=signature_path,
        validators=[validate_image],
        null=True,
        blank=True)

    def save(self, **kwargs):
        """ Save uploaded signature as 350X100 png sig.png """
        super(NormalUser, self).save()
        # Check for first and last name
        if not self.nickname or self.nickname == '':
            # Set initial nickname to first and last name
            if self.user.first_name or self.user.last_name:
                self.nickname = '{0} {1}'.format(
                    self.user.first_name, self.user.last_name)
            elif self.user.username:
                self.nickname = self.user.username
            elif self.user.email:
                self.nickname = self.user.email.split('@')[0]
            else:
                self.nickname = 'Anonymous'
            self.save(update_fields=['nickname'])
        if self.pk is not None:
            # Signature image was submitted for upload
            if self.signatureImage:
                with storage.open(self.signatureImage.name, 'rb+') as original:
                    with open('temp.png', 'wb+') as temp:
                        shutil.copyfileobj(original, temp)

                with Image(filename='temp.png') as sig:
                    sig.resize(350, 100)
                    sig.format = 'png'
                    sig.save(filename='temp.png')

                with storage.open(self.signatureImage.name, 'wb+') as resized:
                    with open('temp.png', 'rb+') as temp:
                        shutil.copyfileobj(temp, resized)
                os.remove('temp.png')

    def __str__(self):
        return self.user.email

class Award(models.Model):
    """ A Certificate """

    awardTemplate = models.CharField(max_length=1024)
    awardType = models.CharField(max_length=50)

    def __str__(self):
        return self.awardType

def ae_path(instance, filename):
    """ Generate filepath for a certificate image """

    retval = 'teamiota/certThumbs/{0}.{1}'.format(instance.id, 'png')
    return retval

class AwardEvent(models.Model):
    """ Meta Data for an instance of an Award being awarded """

    awarder = models.ForeignKey(
        NormalUser,
        related_name='awardER',
        null=True,
        on_delete=models.CASCADE)
    awardee = models.ForeignKey(
        NormalUser,
        related_name='awardEE',
        on_delete=models.CASCADE)
    awardType = models.ForeignKey(Award, on_delete=models.CASCADE)
    dateOfAward = models.DateField()
    certThumbnail = models.ImageField(upload_to=ae_path, null=True)

    def get_absolute_url(self):
        """ AwardEvent URL opens dialog with apropriate image and links """

        return reverse('awardView', kwargs={'pk': str(self.id)})

    def __str__(self):
        return '{0} awarded {1} to {2}'.\
               format(
                   self.awarder.user.email,
                   self.awardType.awardType,
                   self.awardee.user.email)

# Create a NormalUser on new User object
def create_normal_user(sender, instance, created, **kwargs):
    """ Automatically generate NormalUser on new User """

    if created:
        NormalUser.objects.create(user=instance)

# Attach post_save event handler to User save
models.signals.post_save.connect(create_normal_user, sender=User)

# pylint: disable=line-too-long
# src: http://stackoverflow.com/questions/5372934/how-do-i-get-django-admin-to-delete-files-when-i-remove-an-object-from-the-datab
@receiver(models.signals.pre_delete, sender=AwardEvent)
def mymodel_delete(sender, instance, **kwargs):
    """ Delete certificate thumbnail on AwardEvent deletion """

    if os.path.exists(os.path.join(settings.MEDIA_ROOT, str(instance.id) + '.pdf')):
        os.remove(os.path.join(settings.MEDIA_ROOT, str(instance.id) + '.pdf'))
    if os.path.exists(os.path.join(settings.MEDIA_ROOT, str(instance.id) + '.png')):
        os.remove(os.path.join(settings.MEDIA_ROOT, str(instance.id) + '.png'))
    # Pass false so FileField doesn't save the model.
    instance.certThumbnail.delete(False)
