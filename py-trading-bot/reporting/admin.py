from django.contrib import admin
from django.apps import apps
from reporting.models import *

admin.site.register(Report)
admin.site.register(ActionReport)
admin.site.register(Alert)
admin.site.register(ListOfActions)

