# -*- coding: utf-8 -*-
"""
Created on Tue Jan 10 18:09:18 2023

@author: Chris
"""

import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
import datetime

def get_value_line(data):
    data['value'] = 0
    data.loc[data.index[0], 'value'] = 1000
    for i in range(1, len(data)):
        if not np.isnan(data.loc[data.index[i], 'profit']):
            profit = data.loc[data.index[i], 'profit']
            data.loc[data.index[i], 'value'] =\
                data.loc[data.index[i-1], 'value']*(1+profit)
        else:
            data.loc[data.index[i], 'value'] = data.loc[data.index[i-1], 'value']

    return data

def get_benchmark_line(data, apr):

    rate = 1 + (apr/365)*(7/5)
    line = [1000]
    for i in range(len(data)-1):
        line.append(line[i]*rate)

    return line

def get_sp500_line(data):

    date_start = data.index[0]
    date_end = data.index[-1] + datetime.timedelta(days=1)
    interval = '1d'
    # Plot long hold position for S&P500 (not leveraged)
    data_sp = yf.download('SPY', start=date_start, end=date_end, interval=interval)
    data_sp['hold'] = 1000/data_sp.iloc[0,:].Close*data_sp['Close']
    # x0 = np.array(data_sp.index[1:])
    y0 = np.array(data_sp.hold)

    return y0

def plot_value(data, n):
    # Plot value line over constant value lines
    value = int(data.value[len(data)-1])
    num_trades = len(data[data.profit != 0])
    num_wins = len(data[data.profit > 0])
    
    if num_trades > 0:
        win_rate = int((num_wins / num_trades)*100)
        print(f"executed {num_trades} trades")
        print(f"win rate of {win_rate}%")
    else:
        print("no trades made")
    
    plt.rc('lines', linewidth=2.5)
    fig, ax = plt.subplots()
    x = np.array(data.index)
    y = np.array(data.value)
    line, = ax.plot(x, y, label=f"acct=${value}")

    # Make benchmark lines
    line0, = ax.plot(x, get_sp500_line(data), label='S&P500')
    line1, = ax.plot(x, get_benchmark_line(data, 0), label='break even')
    line2, = ax.plot(x, get_benchmark_line(data, .05), label='5% bench')
    line3, = ax.plot(x, get_benchmark_line(data, .10), label='10% bench')
    line4, = ax.plot(x, get_benchmark_line(data, .15), label='15% bench')
    line5, = ax.plot(x, get_benchmark_line(data, .20), label='20% bench')
    line6, = ax.plot(x, get_benchmark_line(data, .25), label='25% bench')
    line7, = ax.plot(x, get_benchmark_line(data, .30), label='30% bench')
    line8, = ax.plot(x, get_benchmark_line(data, .35), label='35% bench')
    # line9, = ax.plot(x, get_benchmark_line(data, .40), label='40% bench')
    
    ax.legend(handlelength=4)
    plt.title(f"{n} ETFs, {num_trades} trades, {win_rate}%win")
    plt.show()