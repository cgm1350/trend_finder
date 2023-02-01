# -*- coding: utf-8 -*-
"""
Created on Sat Jan 21 10:38:37 2023

@author: Chris
"""
import yfinance as yf
import pandas as pd
# import pandas_datareader as web
import datetime

from entry_functions import set_buy_above_ema_rsi_below_30
from entry_functions import set_blackout_dates

from indicator_functions import get_basic_indicators
from indicator_functions import get_double_red
from indicator_functions import get_open_below_prev_close
from indicator_functions import get_rsi_peak

date_start = "2022-01-01"
tomorrow = datetime.datetime.today() + datetime.timedelta(days=1)
date_end = tomorrow.strftime('%Y-%m-%d')
interval = "1d"
n = 500

# Download and save data
sp500_tickers = pd.read_csv('stock_data/sp500_tickers.csv')
tickers = sp500_tickers.Symbol.unique().tolist()[0:n]

# Remove bad tickers
rem_ticker = ('CAH')
if rem_ticker in tickers:
    tickers.remove(rem_ticker)

sp500 = yf.download(tickers, start=date_start, end=date_end, interval=interval)
valid_buys = []
atr_ov_ema = []

for ticker in tickers:
    i = tickers.index(ticker)
    print(f"checking ticker {ticker} ({i} of 500)")
    data = sp500.loc[:, sp500.columns.get_level_values(1) == ticker].copy()
    data.columns = data.columns.droplevel(1)
    data = data[~data.Close.isna()]

    # Get indicators
    data = get_basic_indicators(data)
    data = get_double_red(data)
    data = get_open_below_prev_close(data, 5)
    data = get_rsi_peak(data, 10)
    
    #  Set entry strategy
    data['entry'] = set_buy_above_ema_rsi_below_30(data.ema200, data.rsi, data.Low)
    data['price_entry'] = data.Open

    # Set entry cancels
    data['dlbred_obpc'] = data.dbl_red*data['5p_obpc']
    data = set_blackout_dates(data, 'dlbred_obpc', 10)
    

    if data.entry[-1]:
        print(f"found buy signal today for ticker {ticker}")
        valid_buys.append(ticker)
        atr_ov_ema.append(data.atr[-1] / data.ema200[-1])