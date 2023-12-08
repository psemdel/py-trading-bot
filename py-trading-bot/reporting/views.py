from django.shortcuts import render, redirect
from django.http import HttpResponse
from reporting.telegram import start, cleaning_sub
# Create your views here.
from reporting.models import Report, ActionReport, Alert, OrderExecutionMsg 
from orders.models import Action, StockStatus, exchange_to_index_symbol, ActionSector, StockEx
from orders.ib import actualize_ss

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
def daily_report_sub(
        exchange:str,
        it_is_index:bool=False,
        **kwargs):
    
    if exchange is not None:
        report1=Report.objects.create(stock_ex=StockEx.objects.get(name=exchange))
    else:
        report1=Report.objects.create()
    report1.daily_report(exchange=exchange,it_is_index=it_is_index,**kwargs)
    
    oems=OrderExecutionMsg.objects.filter(report=report1)
    for oem in oems:
        print(oem.text)
    if report1.text:
        print(report1.text)     

def daily_report(
        request,
        exchange:str,
        **kwargs):
    '''
    Write report for an exchange and/or sector
    Identical to the telegrambot function, but here without bot, so sync instead of async
    Either for test purpose, or if your telegram was stopped
    
    Arguments
   	----------
       request: incoming http request
       exchange: name of the stock exchange
    '''  
    s_ex=StockEx.objects.get(name=exchange)
    a="strategies_in_use"
    print("writting daily report "+s_ex.name)
    if s_ex.presel_at_sector_level:
        for sec in ActionSector.objects.all():
            strats=getattr(sec,a).all()
            if len(strats)!=0: #some strategy is activated for this sector
                print("starting report " + sec)
                daily_report_sub(s_ex.name,sec=sec)
    else:
        strats=getattr(s_ex,a).all()
        if len(strats)!=0: 
            daily_report_sub(s_ex.name)

    daily_report_sub(exchange=None,symbols=[exchange_to_index_symbol(s_ex.name)[1]],it_is_index=True)
    return render(request, 'reporting/success_report.html')

def cleaning(request):
    '''
    Deactivate the alert at the end of the day
    '''
    cleaning_sub()
        
    return HttpResponse("cleaning done")

def actualize_ss_view(request):
    actualize_ss()
    return HttpResponse("Stock status actualized")

def create_ss_sub():
    for a in Action.objects.all():
        ss, created=StockStatus.objects.get_or_create(action=a)

def create_ss(request):
    create_ss_sub()
    return HttpResponse("Stock status created")

def test_order(request):
    symbol=""
    strategy=""
    exchange="XETRA"
    short=False
    return render(request, 'reporting/success_report.html')
    #with MyIB() as myIB:
    #    return myIB.entry_order(symbol,strategy, exchange,short), True
    
    return HttpResponse("test")

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