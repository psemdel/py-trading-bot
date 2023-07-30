# Optimization
Optimization algorithms are important to determine the best set of parameters or the best combination of signals for a [strategy](https://github.com/psemdel/py-trading-bot/blob/main/docs/strategies.md) for a given set of stocks. The optimization must moreover avoid overfitting.

The optimization scripts provided must be started by opt_starter.py (in the root). Several scripts are provided, but obviously they are only examples (no guarantee here!). The only thing that matters here is the resulting strategy, the optimization algorithm is just a mean.

In opt_main, the set will be split in a learning and a test set. By comparing the results on both set, you can verify how reliable is your strategy. By default this split is made on the time (`split_learn_train=time`). You can also split on the symbols (`split_learn_train=symbol`).

Most of the algorithm will make evolve the strategy array until it cannot be improved anymore. The starting array can be defined by setting `predefined=False`, the array is then given in `a_simple` if no trend is considered or in `a_bull`, `a_bear` and `a_uncertain`. If no starting array is defined, a random one will be generated. The process is performed several time in a row. The number of iterations is defined by the parameter `loops`. To be sure that your optimization met one of the best possible combination, it is recommended to perform many loops (it is a typical local extremum vs global extremum issue). 

Results are written in opt/output/strat.txt.

## opt_strat
Opt_strat aims at optimizing a strategy for one stock on a given set of stocks.

## opt_sl
Try to find out the best stop loss threshold for a given strategy.

## opt_macro
Optimize the parameters for the trend calculation in order to have maximum return during the bull trend and minimum return during the bear trend.

## Correlation
The following optimization algorithms try to group some stocks together depending on their price correlation and to optimize a strategy for each of those groups.

### opt_symbols
The initial group to be splited is given as a list of symbols.

### opt_cor
The initial group of stocks is defined in constants.py.

### opt_by_part and opt_by_part_rec
The stocks are not grouped depending on their correlation but on their performance on a given strategy. The best are packed together, the rest is  re-optimized.

