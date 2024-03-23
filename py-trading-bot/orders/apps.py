from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders'
    
    def ready(self):
        #if stock status are not defined they need to be created
        from orders.models import StockStatus
        from reporting.views import create_ss_sub
        
        try:
            if len(StockStatus.objects.all())==0:
                create_ss_sub()
        except:
            pass
        