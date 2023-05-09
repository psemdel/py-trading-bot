# Periodic update
Portfolio management needs often update on regular basis of the portfolio, for instance every 15 or 30 days. 

For this purpose, create the update function in reporting/telegram.py. Adapt the function actualize_job if necessary. In the admin panel, create as many jobs as couple strategy/stock_exchange which needs to be covered by the this function. Set frequency_days with the number of days between each update. Period_year defines the number of year which is required to download to perform the calculation. Notes that low figure, can lead to poor result if your optimization functions use some kind of smoothing. In the contrary, high number of years lead to longer calculation and also excluse including stocks recently introduced on the stock exchanges in the calculation.
