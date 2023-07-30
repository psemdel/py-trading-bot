# Periodic update
Portfolio management needs often update on regular basis of the portfolio, for instance every 15 or 30 days. Those strategies have the suffix "slow" in the presel.py file.

To update the candidates, you need to create a job for each of them and each stock exchange where they are used. They will update the objects "Candidates" in the database.

After having started the bot click on "Admin panel" (http://localhost:8000/admin/). 

- Click on "add" close to "Jobs"

Following inputs can be defined:

- strategy: associated strategy
- stock_ex: associated stock exchange 
- frequency_days: how often must the job be executed? In days
- period_year: how far in the past should the script download prices. Notes that low figure, can lead to poor result if your optimization functions use some kind of smoothing. In the contrary, high number of years lead to longer calculation and also excluse including stocks recently introduced on the stock exchanges in the calculation.

The telegram bot will execute automatically those jobs if `UPDATE_SLOW_STRAT` is set to True (which is the default value) in trading_bot/settings.py.

