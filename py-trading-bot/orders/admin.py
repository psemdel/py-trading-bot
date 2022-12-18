from django.contrib import admin
from orders.models import *

admin.site.register(Currency)  
admin.site.register(Fees)
admin.site.register(StockEx)
admin.site.register(Action)
admin.site.register(Order)
admin.site.register(PF)
admin.site.register(ActionCategory)
admin.site.register(ActionSector)
admin.site.register(Strategy)
admin.site.register(Capital)
admin.site.register(OrderCapital)
admin.site.register(Candidates)
admin.site.register(Excluded)
admin.site.register(StratCandidates)

# Register your models here.
