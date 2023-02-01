# -*- coding: utf-8 -*-
"""
Created on Tue Jan  3 18:04:01 2023

@author: Chris
"""

# %% Imports

# ?talib.AROON
# dir(talib)
# talib.get_functions()

import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import math

from entry_functions import set_buy_macd_crossup
from entry_functions import set_buy_macd_crossup_above_ema
from entry_functions import set_buy_above_ema_rsi_below_30
from entry_functions import set_blackout_dates
from entry_functions import set_buy_cancel_oapc
from entry_functions import set_buy_dbl_bot_breakpull

from indicator_functions import get_basic_indicators
from indicator_functions import get_n_day_high
from indicator_functions import get_n_day_low
from indicator_functions import get_double_bottoms
from indicator_functions import get_break_pulls
from indicator_functions import calc_macd_cross
from indicator_functions import get_macd_crosses
from indicator_functions import get_double_red
from indicator_functions import get_open_below_prev_close
from indicator_functions import get_rsi_peak

from plot_functions import get_value_line
from plot_functions import plot_value
from trade_functions import execute_trades
from trade_functions import execute_multi_entry

# # Download and save data
sp500_tickers = pd.read_csv('stock_data/sp500_tickers.csv')
# data = yf.download(sp500_tickers.Symbol.to_list(), start=date_start, end=date_end, interval=interval)
# # data = yf.download('AAPL', start=date_start, end=date_end, interval=interval)
# data.to_pickle('sp500_2022-2012.pkl')

# Compute indicators and re-save data
# df_market = pd.read_pickle('stock_data/sp500_2012-2022.pkl')
# tickers = df_market.loc[:,'Close'].columns.to_list()
# for ticker in tickers:
#     data = df_market.loc[:, df_market.columns.get_level_values(1) == ticker].copy()
#     data['ticker'] = ticker
#     data.columns = data.columns.droplevel(1)
#     data = data[~data.Close.isna()]
#     if len(data) != 0:
#         data = get_basic_indicators(data)
#         data = get_double_red(data)
#         data = get_open_below_prev_close(data, 5)
#         data = get_rsi_peak(data, 10)
#         data = get_n_day_low(data, 5)
#         data = get_n_day_low(data, 7)
#         data = get_n_day_high(data, 5)
#         data = get_double_bottoms(data)
#         data = get_break_pulls(data)
    
#         if ticker == tickers[0]:
#             dfx = data.copy().reset_index()
#         else:
#             dfx = dfx.append(data.copy().reset_index())

# outfile = 'stock_data/sp500_2012-2022_ext2.pkl'
# dfx.to_pickle(outfile)

# df_market = pd.read_pickle(outfile)
# a = df_market[df_market.ticker == ticker].copy().set_index('Date')
# %% Primary inputs
# ticker = 'BA'
date_start = "2001-03-21"
date_end = "2012-12-30"
interval = "1d"
n = 500
# date_start = "2021-01-01"
# date_end = "2021-12-31"
# interval = "60m"
# tickers = ['BA', 'GOOG']
# ticker = 'DFEN'

# sp500 = pd.read_pickle('stock_data/sp500_2012-2022.pkl')
# tickers = sp500.loc[:,'Close'].columns.to_list()[0:n]

sp500 = pd.read_pickle('stock_data/sp500_2012-2022_ext.pkl')
tickers = sp500.ticker.unique().tolist()[0:n]

def test_strategy(ticker, date_start, date_end, interval, sp500):
    # data = yf.download(ticker, start=date_start, end=date_end, interval=interval)
    # data = sp500.loc[:, sp500.columns.get_level_values(1) == ticker].copy()
    data = sp500[sp500.ticker == ticker].copy().set_index('Date')
    # data.columns = data.columns.droplevel(1)
    data = data[~data.Close.isna()]

    # Get indicators
    # data = get_basic_indicators(data)
    # data = get_n_day_low(data, 5)
    # data = get_n_day_low(data, 7)
    # data = get_n_day_high(data, 5)
    # data = get_double_bottoms(data)
    # data = get_break_pulls(data)
    # data = get_macd_crosses(data)
    # data = get_double_red(data)
    # data = get_open_below_prev_close(data, 5)
    # data = get_rsi_peak(data, 10)
    
    #  Set entry strategy
    # data['entry'] = data.cdl_hammer.apply(lambda x: True if x==100 else False)
    # data['entry'] = data.cdl_3inside.apply(lambda x: True if x==-100 else False)
    # data['entry'] = data['20d_high'].apply(lambda x: True if x=='x' else False)
    # data['entry'] = set_buy_macd_crossup(data.macd, data.macd_crossup)
    # data['entry'] = set_buy_macd_crossup_above_ema(data.macd, data.macd_crossup,
    #                                                data.Close, data.ema200)
    data = set_buy_dbl_bot_breakpull(data)
    # data['entry'] = set_buy_above_ema_rsi_below_30(data.ema200, data.rsi, data.Low)
    data['price_entry'] = data.Open

    # # Set entry cancels
    # data['dlbred_obpc'] = data.dbl_red*data['5p_obpc']
    # data = set_buy_cancel_oapc(data, .02)
    # data = set_blackout_dates(data, 'dlbred_obpc', 10)
    data.entry =\
        data.apply(lambda x: False if math.isnan(x.atr) else x.entry, axis=1)
    
    # Set exit strategy
    exit_strategy = {}
    exit_strategy['target_stop'] = '-'
    # exit_strategy['max_days'] = 10
    # exit_strategy['rsi_peak'] = 40
    a_high = 3.0
    a_low = 1.0
    data['target_atr'] = a_high*data.atr + data.price_entry
    data['stop_atr'] = data.price_entry - a_low*data.atr
    
    # Execute trades & plot profit
    data['profit'] = 0
    data[['entered', 'exit']] = False
    data = execute_trades(data, exit_strategy)
    
    return data

# Loop through tickers and aggregate entry opportunities
i = 0
for ticker in tickers:

    print('running ticker = ' + ticker + ' ' + str(i) + ' of ' + str(n-1))
    i = i + 1
    data_i = test_strategy(ticker,  date_start, date_end, interval, sp500)
    data_i[ticker] = data_i.apply(lambda x: 100 if x.entered else 0, axis=1)
    data_i[ticker] = data_i.apply(lambda x: x.profit if x.profit != 0 else x[ticker], axis=1)

    if ticker == tickers[0]:
        dfx = data_i.rename(columns={'trade': ticker})[ticker]
    elif ticker == tickers[1]:
        dfx = pd.merge(dfx, data_i[ticker], how='left', left_index=True, right_index=True)
    else:
        dfx = dfx.merge(data_i[ticker], how='left', left_index=True, right_index=True)

# Calculate volatility metric for multi-entry stock selection
sp500['atr_ov_ema'] = sp500.atr / sp500.ema200
sp500_vol = sp500[['date', 'ticker', 'atr_ov_ema']].set_index('date')

# Determine profit from aggregate trades
dfx['entry'] = dfx.apply(lambda x: True if x.max() == 100 else False, axis=1)
dfx = execute_multi_entry(dfx, sp500_vol)
dfx['entered'] = dfx.entry

x = get_value_line(dfx.copy())
plot_value(x, n)

outfile = 'C:\\Users\\Chris\\anaconda3\\user\\trading\\data.csv'
x.to_csv(outfile)
