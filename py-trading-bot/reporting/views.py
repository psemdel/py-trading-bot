from django.shortcuts import render, redirect
from django.http import HttpResponse
from reporting.telegram import start
# Create your views here.
from reporting.models import Report, ActionReport, Alert, ListOfActions
from orders.models import Action, exchange_to_index_symbol
from trading_bot.settings import _settings

from .filter import ReportFilter

def reportsView(request): 
    reports= Report.objects.all()
    context={'reports': ReportFilter(request.GET, queryset=reports)}
    return render(request, 'reporting/reports.html', context)

def reportView(request,pk):
    report= Report.objects.filter(id=pk)
    ars=ActionReport.objects.filter(report=pk)

    context={'report':report[0], 'ars':ars}
    return render(request, 'reporting/report.html', context)

def dailyView(request):
    report= Report.objects.latest('id')
    actions=ActionReport.objects.filter(report=report.id)
    indexes=ActionReport.objects.filter(report=report.id)
    context={'report':report, 'actions':actions, 'indexes':indexes}
    return render(request, 'reporting/report.html', context)
    
def trendView(request,pk): 
    report= Report.objects.filter(id=pk)
    ars=ActionReport.objects.filter(report=pk)
    
    context={'report':report[0], 'ars':ars}
    return render(request, 'reporting/trend.html', context)

def alertsView(request): 
    alerts= Alert.objects.filter(active=True)
    context={'alerts':alerts}
    return render(request, 'reporting/alerts.html', context)

#manual start to avoid multiple instanciation
def start_bot(request):
    start()
    print("bot_start ok")
    return redirect('reporting:reports')

#For testing purpose
def daily_report_sub(exchange,**kwargs):
    report1=Report()
    report1.save()
    
    st=report1.daily_report_action(exchange,**kwargs)
    if st is None:
        raise ValueError("The creation of the strategy failed, report creation interrupted")
        
    report1.presel(st,exchange,**kwargs)
    report1.presel_wq(st,exchange,**kwargs)
    send_order_test(report1)
    
def daily_report_index_sub(indexes):
    report3=Report()
    report3.save()    

    report3.daily_report_index(indexes) # "BZ=F" issue
    send_order_test(report3)

def daily_report(**kwargs):
    try:
        short_name=kwargs.get("short_name")
        key=kwargs.get("key")
        print("writting daily report "+short_name)
        for exchange in _settings[key]:
            if exchange=="NYSE":
                for s in _settings["NYSE_SECTOR_TO_SCAN"]:  
                    print("starting report " + s)
                    daily_report_sub("NYSE",sec=s)
            else:
               daily_report_sub(exchange)

        indexes=[exchange_to_index_symbol(exchange)[1] for exchange in _settings[key]]
        daily_report_index_sub(indexes)
        
        return HttpResponse("report written")

    except Exception as e:
        print(e)
        pass

def trigger_17h(request):
    return daily_report(short_name="17h",key="17h_stock_exchanges")
    
def trigger_22h(request):
    return daily_report(short_name="22h",key="22h_stock_exchanges")

def send_order_test(report):
    for auto in [False, True]:
        for entry in [False, True]:
            for short in [False, True]:
                try:
                    ent_ex_symbols=ListOfActions.objects.get(report=report,auto=auto,entry=entry,short=short)
                    for a in ent_ex_symbols.actions.all():
                        send_entry_exit_msg_test(a.symbol,entry,short,auto) 
                except:
                    pass

    if report.text:
         print(report.text)      
    
def send_entry_exit_msg_test(symbol,entry,short, auto):
    if auto:
        part1=""
        part2=""
    else:
        part1="Manual "
        part2="requested for "
    
    if entry:
        part1+="entry "
    else:
        part1+="exit "
        
    if short:
        part3=" short"
    else:
        part3=""
        
    print(part1+part2+symbol + " "+ part3) 

def cleaning(request):
    alerts=Alert.objects.filter(active=True)
    for alert in alerts:
        alert.active=False
        alert.save()
        
    return HttpResponse("cleaning done")

def test_order(request):
    symbol=""
    strategy=""
    exchange="XETRA"
    short=False
    
    #with MyIB() as myIB:
    #    return myIB.entry_order(symbol,strategy, exchange,short), True
    
    return HttpResponse("test order done")

def test(request):
    from ib_insync import Stock
    import vectorbtpro as vbt
        
    import logging
    from orders.ib import place
    #logger = logging.getLogger(__name__)
    action=Action.objects.get(symbol="IBM")
    txt, _, _= place(True,
                            action,
                            False,
                            order_size=15000)
    #action=Action.objects.get(symbol="EN.PA")
    #myIB=MyIB()
    
    #contract = Stock(action.ib_ticker,action.stock_ex.ib_ticker, action.currency.symbol)
    #myIB.get_past_closing_price(contract)
    #cours_open, cours_close, cours_low, cours_high=retrieve_data(["EN.PA","DG.PA"],"1y")
    #macd=vbt.MACD.run(cours_close)
    #print(macd.macd)
    #print(myIB.positions())
    
    
    #check_hold_duration("KER.PA",False,key="retard")
    #report=Report(ent_symbols=[],ex_symbols=[])
    #report.save()
    #report.daily_report_17h()
    
    #
    #myIB.test("OR.PA")
    #myIB.entry_order("OR.PA",False,strat19=True)
    #myIB.exit_order("OR.PA",False,strat19=True)
    #print(myIB.ib.accountSummary())
    #print(myIB.ib.accountValues())
    #print(myIB.ib.positions())

    #retrieve('AAPL',"10 D")    
    #myIB.disconnect()
    
    return HttpResponse("test ok")