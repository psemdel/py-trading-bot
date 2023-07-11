from django.shortcuts import render
from orders.models import StockStatus, Order, Strategy, StratCandidates, pf_retrieve_all
from orders.form import ManualOrderForm
from django.db.models import Q
#from django.http import HttpResponse
# Create your views here.

def pf_view(request):
    form=ManualOrderForm(request.POST or None)
    
    if request.method == 'POST':
        if form.is_valid():
            action=Strategy.objects.get(name=form.cleaned_data["action"])
            st=Strategy.objects.get(name=form.cleaned_data["strategy"])
            short=form.cleaned_data["short"]
            
            c1=Q(action=action)
            c2=Q(strategy=st)
            c3=Q(short=form.cleaned_data["short"])  
            c4= Q(active=True)

            if "closing" in request.POST:
                closing(action,st, c1, c2, c3, c4)
            elif "opening" in request.POST:    
                opening(form, action, st, short)
            elif "reverse" in request.POST:
                closing(action,st, c1, c2, c3, c4)
                opening(form, action, st, not short)
    else:
        form = ManualOrderForm(initial={'sl_threshold': 0, "daily_sl_threshold":0, "short":False})

    context={'actions':pf_retrieve_all(),"form":form}            
    
    return render(request, 'orders/pf.html', context)

def opening(form, action, st, short):
    o=Order.objects.create(short=short, action=action, strategy=st)
    if (form.cleaned_data["sl_threshold"] is not None and form.cleaned_data["sl_threshold"]!=0):
        o.sl_threshold=form.cleaned_data["sl_threshold"]
        o.save()
    
    if (form.cleaned_data["daily_sl_threshold"] is not None and form.cleaned_data["daily_sl_threshold"]!=0):
        print(form.cleaned_data["daily_sl_threshold"])
        o.daily_sl_threshold=form.cleaned_data["daily_sl_threshold"]
        o.save()
        
    ss=StockStatus.objects.get(action=action)
    ss.order_in_ib=False
    ss.strategy=st
    if form.cleaned_data["short"]:
        ss.quantity=-1
    else:
        ss.quantity=1
    ss.save()
    
    sc=StratCandidates.objects.filter(strategy=st) #keep consistency
    if len(sc)>0:
        if action not in sc[0].actions.all():
            sc[0].actions.add(action)    
 
def closing(action,st, c1, c2, c3, c4):
    orders=Order.objects.filter(c1 & c2 & c3 & c4)
    if len(orders)==0:
        raise ValueError("Order not found")
    elif len(orders)>1:
        raise ValueError("Several orders found, do the step manually in the admin panel")
    else:
        o=orders[0]
    
    o.active=False
    o.save()
    
    ss=StockStatus.objects.get(action=action)
    ss.order_in_ib=False
    ss.strategy=st
    ss.quantity=0
    ss.save()

