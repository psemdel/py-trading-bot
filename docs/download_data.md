# Downloading data
The bot comes with some data saved in saved_cours. The naming convention is "name of the index" followed by the period.

To download more data, go in core/data_manager.py. At the bottom, you can select which stock exchange list for which period you want to download. You can obvious create your own list of symbols in constants.py. After running the script, you will have one file "<symbol_index>"_period.h5" in saved_cours. You can rename the period in the correct time.

You can then use your data in the Jupyter notebooks like strat.ipynb:

    ```
    period="2007_2022_08"
    symbol_index="CAC40"
    ust=strat.StratHold(period,symbol_index=symbol_index)    
    ```
    
This will load the stock file CAC40_2007_2022_08.

