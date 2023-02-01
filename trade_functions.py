# -*- coding: utf-8 -*-
"""
Created on Tue Jan 10 18:09:44 2023

@author: Chris
"""

import datetime
import math

def execute_trades(data, exit_strategy):

    data_rem = data.copy()
    one_day = datetime.timedelta(days=1)

    # Loop through all entries and find exit & corresponding profit
    b = 0
    while len(data_rem[data_rem.entry]) > 1:
        
        date_entry = data_rem[data_rem.entry].index[0] + one_day
        df_entry = data_rem.loc[date_entry:,:].copy()
        date_entry = df_entry.index[0]
        data.loc[date_entry, 'entered'] = True

        price_entry = df_entry.iloc[0].Open
        # i = data.index.get_loc(date_entry) - 1
        # price_entry = data.iloc[i].Close
        df_entry['exit'] = False

        # Find target/stop triggers
        if 'target_stop' in exit_strategy.keys():
            # Exit if target or stop is hit on any day after entry date
            target_atr = df_entry.iloc[0].target_atr
            stop_atr = df_entry.iloc[0].stop_atr
        
            df_entry['trig_target_atr'] =\
                df_entry.apply(lambda x: True if x.High > target_atr else False,
                               axis=1)
            df_entry['trig_stop_atr'] =\
                df_entry.apply(lambda x: True if x.Low < stop_atr else False,
                               axis=1)
        else:
            df_entry['trig_target_atr'] = False
            df_entry['trig_stop_atr'] = False

        if 'max_days' in exit_strategy.keys():
            # Exit after a specified numer of maximum trading days
            df_entry['trig_target_maxdays'] = False
            max_days = exit_strategy['max_days']
            df_entry['target_max_days'] = df_entry.Close
            df_entry.loc[df_entry.iloc[max_days+1:].index,
                         'trig_target_maxdays'] = True

        if 'rsi_peak' in exit_strategy.keys():
            # Exit when rsi goes above specified value
            df_entry['trig_target_rsi'] =\
                df_entry.apply(lambda x: True if x.High > x.target_rsi\
                                else False, axis=1)
            # df_entry['trig_target_rsi'] =\
            #     df_entry.apply(lambda x: True if x.rsi >= 40\
            #                     else False, axis=1)

        # Set exit if any triggers found
        cols = [k for k in df_entry.columns.to_list() if 'trig' in k]
        trig = df_entry.loc[:, cols]
        df_entry['exit'] = trig[cols].any(axis=1)
        
        if len(df_entry[df_entry.exit]) == 0:
            # No valid exits remaining
            date_exit = df_entry.index[-1]
        else:
            date_exit = df_entry[df_entry.exit].index[0]
            if df_entry.loc[date_exit, 'trig_stop_atr']:
                price_exit = stop_atr
            elif df_entry.loc[date_exit, 'trig_target_atr']:
                price_exit = target_atr
            elif df_entry.loc[date_exit, 'trig_target_rsi']:
                price_exit = df_entry.loc[date_exit, 'Close']
            elif df_entry.loc[date_exit, 'trig_target_maxdays']:
                price_exit = df_entry.loc[date_exit, 'target_max_days']

            profit = (price_exit - price_entry)/price_entry
            if profit == 0:
                profit = .0001
            data.loc[date_exit, 'profit'] = profit
            data.loc[date_exit, 'exit'] = True
        
        data_rem = data.loc[date_exit:,:].iloc[1:,:]
        b = b + 1

    return data


def execute_multi_entry(data, vol):

    data['profit'] = 0
    data_rem = data.copy()

    # Loop through all entries and find exit & corresponding profit
    while len(data_rem[data_rem.entry]) != 0:

        date_entry = data_rem[data_rem.entry].index[0]
        df_entry = data_rem.loc[date_entry:,:].copy()
        df_date = df_entry.loc[date_entry, :]
        df_buys = df_date[df_date == 100]
        vol_date = vol.loc[date_entry,:].set_index('ticker')
        entry_ticker = vol_date.loc[df_buys.index.to_list(), :].atr_ov_ema.idxmax()
        if type(entry_ticker) != str:
            entry_ticker = df_buys.index[0]
        if len(df_entry[df_entry[entry_ticker]!=0]) > 1:
            date_exit = df_entry[df_entry[entry_ticker]!=0].index[1]
            data.loc[date_exit, 'profit'] = df_entry.loc[date_exit, entry_ticker]
        else:
            date_exit = data_rem.index[-1]

        data_rem = data.loc[date_exit:,:].iloc[1:,:]

    return data
