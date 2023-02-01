# -*- coding: utf-8 -*-
"""
Created on Tue Jan 10 17:39:04 2023

@author: Chris
"""

import datetime
import math

def set_buy_macd_crossup(macd, macd_crossup):
    buy = (macd < 0)*macd_crossup
    return buy

def set_buy_macd_crossup_above_ema(macd, macd_crossup, price, ema):
    buy = (macd < 0)*macd_crossup*(price > ema)
    return buy

def set_buy_above_ema_rsi_below_30(ema, rsi, price):
    buy = (price > ema)*(rsi < 30)
    return buy

def set_buy_dbl_bot_breakpull(data):
    data['entry'] = False
    df_buys = data[data.is_break_pull].copy()
    dates = df_buys.date_entry
    data.loc[dates, 'entry'] = True

    return data

def set_buy_cancel_oapc(data, perc):
    """
    cancel buy signals when open price is more than perc% above prev close
    """

    data_temp = data.copy()
    for i in range(len(data_temp[data_temp.entry])):
        date_entry = data_temp[data_temp.entry].iloc[i, :].date
        price_open = data_temp[data_temp.entry].iloc[i, :].Open
        i_prev_day = data.index.get_loc(date_entry)-1
        prev_close = data.iloc[i_prev_day, :].Close
        if price_open / prev_close - 1 > perc:
            data.loc[date_entry, 'entry'] = False

    return data

def set_blackout_dates(data, trigger, n_days):

    # data['profit'] = 0
    data_rem = data.copy()

    # Loop through all entries and find exit & corresponding profit
    while len(data_rem[data_rem[trigger]]) != 0:

        date_trigger = data_rem[data_rem[trigger]].index[0]
        date_end = date_trigger + datetime.timedelta(days=n_days)
        if data.index[-1] > date_end:
            data.loc[date_trigger:date_end, 'entry'] = False
        else:
            data.loc[date_trigger:data.index[-1], 'entry'] = False

        data_rem = data.loc[date_end:,:].iloc[1:,:]

    return data
