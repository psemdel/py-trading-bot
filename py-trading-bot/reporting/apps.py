from django.apps import AppConfig

class ReportingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reporting'

    #def ready(self): #does not work because it starts with the bot AND the webserver
    #    from reporting.telegram import start
    #    start()
   
