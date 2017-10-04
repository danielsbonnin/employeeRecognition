from django.contrib import admin

from .models import *
# Register your models here.

admin.site.register(Location)
admin.site.register(Department)
admin.site.register(NormalUser)
admin.site.register(Award)
admin.site.register(AwardEvent)
    
