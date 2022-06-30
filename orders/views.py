from django.shortcuts import render
from orders.models import PF, Action
# Create your views here.

def pfView(request):
    pf= PF.objects.filter(short=False)
    pf_short= PF.objects.filter(short=True)
   
    context={'actions':pf[0].actions, 'actions_short':pf_short[0].actions}
    return render(request, 'orders/pf.html', context)