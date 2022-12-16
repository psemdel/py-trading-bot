from django.shortcuts import render, redirect
from django.http import HttpResponse
from reporting.telegram import start
# Create your views here.
from reporting.models import Report, ActionReport, Alert
from core import bt, btP
from orders.models import ActionCategory, StockEx, Action, get_exchange_actions, MyIB


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
def trigger_17h(request):
    try:
        report1=Report()
        report1.save()
    
        st=report1.daily_report_action("Paris")
        if st is None:
            raise ValueError("The creation of the strategy failed, report creation interrupted")    
            
        report1.presel(st,"Paris")
        report1.presel_wq(st,"Paris")
        send_order_test(report1)
        
        report2=Report()
        report2.save()            
    
        st=report2.daily_report_action("XETRA")
        if st is None:
            raise ValueError("The creation of the strategy failed, report creation interrupted")    
            
        report2.presel(st,"XETRA")
        report2.presel_wq(st,"XETRA")
        send_order_test(report2)
        
        report3=Report()
        report3.save()    
    
        report3.daily_report_index(["^FCHI","^GDAXI"]) #"CL=F",
        send_order_test(report3)
    
        return HttpResponse("report written")
    except ValueError as msg:
        print(msg)
#For testing purpose
def trigger_22h(request):
    try:
        report1=Report()
        report1.save()
    
        st=report1.daily_report_action("Nasdaq") 
        if st is None:
            raise ValueError("The creation of the strategy failed, report creation interrupted")    
            
        report1.presel(st,"Nasdaq")
        report1.presel_wq(st,"Nasdaq")
        send_order_test(report1)
        
        for s in ["realestate","industry","it","com","staples","consumer","utilities","energy",\
                  "fin","materials","healthcare"]: 
            print("starting report " + s)      
            report=Report()
            report.save()
        
            st=report.daily_report_action("NYSE",sector=s) 
            report.presel(st,"NYSE",sector=s)
            report.presel_wq(st,"NYSE",sector=s)
            send_order_test(report)
    
        report2=Report()
        report2.save()            
        report2.daily_report_index(["^DJI","^IXIC"])
        send_order_test(report2)
        
        return HttpResponse("report written")
    except ValueError as msg:
        print(msg)
        
def send_order_test(report):
    ent_symbols, ex_symbols, ent_symbols_short, ex_symbols_short,\
    ent_symbols_manual, ex_symbols_manual, ent_symbols_short_manual, ex_symbols_short_manual\
    =report.get_ent_ex_symbols()
    
    if ent_symbols is not None:
        for s in ent_symbols:
            print("entry " + str(s))
    if ex_symbols is not None:
        for s in ex_symbols:
            print("exit " + str(s))
    if ent_symbols_short is not None:
        for s in ent_symbols_short:
            print("entry_short " + str(s))
    if ex_symbols_short is not None:
        for s in ex_symbols_short:
            print("exit_short " + str(s))
    if ent_symbols_manual is not None:
        for s in ent_symbols_manual:
            print("entry " + str(s))
    if ex_symbols_manual is not None:
        for s in ex_symbols_manual:
            print("exit " + str(s))
    if ent_symbols_short_manual is not None:
        for s in ent_symbols_short_manual:
            print("entry_short " + str(s))
    if ex_symbols_short_manual is not None:
        for s in ex_symbols_short_manual:
            print("exit_short " + str(s))
            
def actualize_hist_paris(request):
    symbols=get_exchange_actions("Paris")
    presel=btP.Presel(symbols1=symbols,period1="1y",exchange="Paris")
    presel.actualize_hist_vol_slow("Paris")
    
    return HttpResponse("candidates actualised")

def actualize_hist_xetra(request):
    symbols=get_exchange_actions("XETRA")
    presel=btP.Presel(symbols1=symbols,period1="1y",exchange="XETRA")
    presel.actualize_hist_vol_slow("XETRA")
    
    return HttpResponse("candidates actualised")

def actualize_hist_nasdaq(request):
    symbols=get_exchange_actions("Nasdaq")
    presel=btP.Presel(symbols1=symbols,period1="1y",exchange="Nasdaq")
    presel.actualize_hist_vol_slow("Nasdaq")
    
    return HttpResponse("candidates actualised")

def actualize_realmadrid_paris(request):
    symbols=get_exchange_actions("Paris")
    presel=btP.Presel(symbols1=symbols,period1="4y",exchange="Paris")
    presel.actualize_realmadrid("Paris")
    
    return HttpResponse("candidates actualised")

def actualize_realmadrid_xetra(request):
    symbols=get_exchange_actions("XETRA")
    presel=btP.Presel(symbols1=symbols,period1="4y",exchange="XETRA")
    presel.actualize_realmadrid("XETRA")
    
    return HttpResponse("candidates actualised")

def actualize_realmadrid_nasdaq(request):
    symbols=get_exchange_actions("Nasdaq")
    presel=btP.Presel(symbols1=symbols,period1="4y",exchange="Nasdaq")
    presel.actualize_realmadrid("Nasdaq")
    
    return HttpResponse("candidates actualised")

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
    
    with MyIB() as myIB:
        return myIB.entry_order(symbol,strategy, exchange,short), True
    
    return HttpResponse("test order done")

def test(request):
    from orders.models import MyIB, retrieve_data
    from ib_insync import Stock
    import vectorbt as vbt
        
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