from django.shortcuts import render
from orders.models import PF, Order, OrderCapital
from orders.form import ManualOrderForm
from django.db.models import Q
from django.http import HttpResponse
# Create your views here.

def pf_view(request):
    form=ManualOrderForm(request.POST or None)
    context={'pfs':PF.objects.all(),"form":form}
    if request.method == 'POST':
        if form.is_valid():
            action=form.cleaned_data["action"]
            c1=Q(strategy=form.cleaned_data["strategy"])
            c2=Q(stock_ex=action.stock_ex)
            c3=Q(short=form.cleaned_data["short"])  
            c4=Q(sector=form.cleaned_data["sector"])
            c5 =Q(action=action)
            c6= Q(active=True)
            
            pfs=PF.objects.filter(c1&c2&c3&c4)
            #optional
            try:
                oc=OrderCapital.objects.get(c1 & c2 & c4)
            except:
                oc=None
                pass
            
            if len(pfs)==0:
                return HttpResponse("Corresponding pf not found")
            elif len(pfs)>1:
                return HttpResponse("Several corresponding pf found, do the step manually in the admin panel")
            else:
                pf=pfs[0]
            c7= Q(pf=pf)
            
            if "closing" in request.POST:
                orders=Order.objects.filter(c3 & c5 & c6 & c7)
                if len(orders)==0:
                    return HttpResponse("Order not found")
                elif len(orders)>1:
                    return HttpResponse("Several orders found, do the step manually in the admin panel")
                else:
                    o=orders[0]
                
                if oc is not None:
                    oc.capital+=1
                    oc.save()
                
                pf.remove(action.symbol) 
                o.active=False
                o.save()
                
            elif "opening" in request.POST:    
                o=Order.objects.create(short=form.cleaned_data["short"], action=action, pf=pf)
                pf.append(action.symbol) 
                
                if oc is not None:
                    oc.capital-=1
                    oc.save()
    
    return render(request, 'orders/pf.html', context)
