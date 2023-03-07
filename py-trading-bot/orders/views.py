from django.shortcuts import render
from orders.models import PF
# Create your views here.

def pfView(request):
    context={'pfs':PF.objects.all()}
    return render(request, 'orders/pf.html', context)