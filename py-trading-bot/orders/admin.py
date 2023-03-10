from django.contrib import admin
from orders.models import *

admin.site.register(Currency)  
admin.site.register(Fees)

admin.site.register(Order)
admin.site.register(PF)
admin.site.register(ActionCategory)
admin.site.register(ActionSector)
admin.site.register(Strategy)
admin.site.register(OrderCapital)
admin.site.register(Candidates)
admin.site.register(Excluded)
admin.site.register(StratCandidates)

class ActionAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super(ActionAdmin, self).get_form(request, obj, **kwargs)
        etf_long=ActionCategory.objects.get(short="ETFLONG")
        form.base_fields['etf_long'].queryset = Action.objects.filter(category=etf_long)
        etf_short=ActionCategory.objects.get(short="ETFSHORT")
        form.base_fields['etf_short'].queryset = Action.objects.filter(category=etf_short)
        return form

admin.site.register(Action, ActionAdmin)

class StockExAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super(StockExAdmin, self).get_form(request, obj, **kwargs)
        ind=ActionCategory.objects.get(short="IND")
        form.base_fields['main_index'].queryset = Action.objects.filter(category=ind)
        return form
    
admin.site.register(StockEx,StockExAdmin)
# Register your models here.
