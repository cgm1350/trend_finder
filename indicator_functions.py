# -*- coding: utf-8 -*-
"""
Created on Tue Jan 10 18:08:29 2023

@author: Chris
"""

import numpy as np
import pandas as pd
import talib

def get_basic_indicators(data):
    """
    appends standard stock indicators to dataframe
    """

    data['date'] = data.index
    data['atr'] = talib.ATR(data.High, data.Low, data.Close, timeperiod=100)
    data['rsi'] = talib.RSI(data.Close, timeperiod=10)
    data['ema200'] = talib.EMA(data.Close, timeperiod=200)
    # data['ema100'] = talib.EMA(data.Close, timeperiod=100)
    # data['ema50'] = talib.EMA(data.Close, timeperiod=50)
    # data['ema20'] = talib.EMA(data.Close, timeperiod=20)
    # data['macd'], data['macdsignal'], data['macdhist'] = talib.MACD(data.Close, fastperiod=12, slowperiod=26, signalperiod=9)
    # data['cdl_hammer'] = talib.CDLHAMMER(data.Open, data.High, data.Low, data.Close)
    # data['cdl_shstar'] = talib.CDLSHOOTINGSTAR(data.Open, data.High, data.Low, data.Close)
    # data['cdl_3inside'] = talib.CDL3INSIDE(data.Open, data.High, data.Low, data.Close)
    data['cdl_color'] = data.apply(lambda x: 'green' if x.Open < x.Close else 'red', axis=1)
    data['body_high'] = data.apply(lambda x: x.Open if x.cdl_color == 'red' else x.Close, axis=1)

    return data

def get_n_day_high(data, n_days):
    """
    appends indicators for whether closing price on a given day is n day high
    """

    # Initialize dataframe column
    data[str(n_days) + 'd_high'] = '-'

    # Loop through all days and find when close price is n_days max
    for i in range(n_days, len(data)):
        d = np.round((n_days-1)/2, 0)
        high = data.iloc[int(i-d):int(i+d+1)].High.max()
        
        if data.iloc[i].High == high:
            data.loc[data.index[i], str(n_days) + 'd_high'] = 'x'

    return data

def get_n_day_low(data, n_days):
    """
    appends indcators for whether closing price on a given day is n day low
    """

    # Initialize dataframe column
    data[str(n_days) + 'd_low'] = '-'

    # Loop through all days and find when close price is n_days min
    for i in range(n_days, len(data)):
        d = np.round((n_days-1)/2, 0)
        low = data.iloc[int(i-d):int(i+d+1)].Low.min()
        
        if data.iloc[i].Low == low:
            data.loc[data.index[i], str(n_days) + 'd_low'] = 'x'
    return data

def calc_macd_cross(macd, macdsignal, macd_m1, macdsignal_m1):

    today_diff = macd - macdsignal
    yest_diff = macd_m1 - macdsignal_m1
    macd_crossup = (today_diff > 0)*(yest_diff < 0)
    macd_crossdn = (today_diff < 0)*(yest_diff > 0)

    return macd_crossup, macd_crossdn

def get_macd_crosses(data):

    data = get_prev_day_cols(data, ['macd', 'macdsignal'])
    data['macd_crossup'], data['macd_crossdn'] =\
        calc_macd_cross(data.macd, data.macdsignal, data.macd_m1,
                        data.macdsignal_m1)

    return data

def get_double_red(data):
    """
    appends column boolean if day and previous day candles are red
    """

    data = get_prev_day_cols(data, ['cdl_color'])
    data['dbl_red'] = data.apply(lambda x: True if x.cdl_color == 'red' and x.cdl_color_m1 == 'red'
                                 else False, axis=1)

    return data

def get_open_below_prev_close(data, perc):
    """
    appends column boolean if open price is below previous day close price by given percent
    """

    data = get_prev_day_cols(data, ['Close'])
    col = str(int(perc)) + 'p_obpc'
    data[col] = data.apply(lambda x: True if (x.Open - x.Close_m1)/x.Close_m1 < -perc/100
                           else False, axis=1)

    return data

def get_prev_day_cols(data, cols):
    """
    appends new cols to dataframe using the entries from the previous day (row)
    """

    data2 = data.loc[data.index[:-1], cols].copy()
    data2 = data2.reset_index(drop=False)
    data2['Date'] = data.index[1:]
    data2 = data2.set_index('Date')
    
    dict_rename = {}
    for col in cols:
        dict_rename[col] = col + '_m1'

    data2 = data2.rename(columns=dict_rename)
    data = pd.merge(data, data2, left_index=True, right_index=True)

    return data

def get_next_day_cols(data, cols):
    """
    appends new cols to dataframe using the entries from the next day (row)
    """

    data2 = data.loc[data.index[1:], cols].copy().reset_index(drop=True)    
    dict_rename = {}
    for col in cols:
        dict_rename[col] = col + '_p1'

    data2 = data2.rename(columns=dict_rename)
    data = pd.merge(data, data2, left_index=True, right_index=True)

    return data

def get_gain(price1, price2):
    """
    returns a positive gain if price 1 > price 2 otherwise returns 0
    """

    gain = ((price2-price1)>0)*(price2-price1)+0
    return gain

def get_loss(price1, price2):
    """
    returns a positive loss if price 2 > price 1 otherwise returns 0
    """

    loss = ((price1-price2)>0)*(price1-price2)+0
    return loss

def get_rsi_peak(data, per):
    """
    calculates rsi using daily high, as opposed to daily close (trad. rsi)
    """

    date_start = data[~data.Open.isna()].index[0]
    datax = data[date_start:].copy()
    # data = get_prev_day_cols(data, ['Close'])

    datax['gain'] = get_gain(datax.Close_m1, datax.Close)
    datax['loss'] = get_loss(datax.Close_m1, datax.Close)
    datax[['avg_gain', 'avg_loss', 'avg_gain_pk', 'avg_loss_pk']] = 0
    avg_gain_start = datax.iloc[0:per].gain.sum()/per
    avg_loss_start = datax.iloc[0:per].loss.sum()/per

    datax['gain_pk'] = get_gain(datax.Close_m1, datax.High)
    datax['loss_pk'] = get_loss(datax.Close_m1, datax.High)

    datax.loc[datax.index[per], 'avg_gain'] =\
        (datax.loc[datax.index[per], 'gain'] + (per-1)*avg_gain_start)/per
    datax.loc[datax.index[per], 'avg_loss'] =\
        (datax.loc[datax.index[per], 'loss'] + (per-1)*avg_loss_start)/per

    goal_rsi = 40
    goal_rs = 100/(100-goal_rsi)-1
    datax[['rs_pk', 'rsi_pk', 'target_rsi']] = 0

    avg_gain_m1 = datax.loc[datax.index[per], 'avg_gain']
    avg_loss_m1 = datax.loc[datax.index[per], 'avg_loss']
    for i in range(per + 1, len(datax)):
        gain = datax.loc[datax.index[i], 'gain']
        loss = datax.loc[datax.index[i], 'loss']
        gain_pk = datax.loc[datax.index[i], 'gain_pk']
        loss_pk = datax.loc[datax.index[i], 'loss_pk']

        avg_gain = (avg_gain_m1*(per-1) + gain)/per
        avg_loss = (avg_loss_m1*(per-1) + loss)/per
        avg_gain_pk = (avg_gain_m1*(per-1) + gain_pk)/per
        avg_loss_pk = (avg_loss_m1*(per-1) + loss_pk)/per

        datax.loc[datax.index[i], 'avg_gain'] = avg_gain
        datax.loc[datax.index[i], 'avg_loss'] = avg_loss
        datax.loc[datax.index[i], 'avg_gain_pk'] = avg_gain_pk
        datax.loc[datax.index[i], 'avg_loss_pk'] = avg_loss_pk
        
        datax.loc[datax.index[i], 'target_rsi'] =\
            goal_rs*(datax.loc[datax.index[i-1], 'avg_loss']*9) -\
            datax.loc[datax.index[i-1], 'avg_gain']*9 +\
                datax.loc[datax.index[i-1], 'Close']

        avg_gain_m1 = avg_gain
        avg_loss_m1 = avg_loss

    datax['rs_pk'] = datax.avg_gain_pk / datax.avg_loss_pk
    datax['rsi_pk'] = 100 - 100/(1+datax.rs_pk)
    
    data['target_rsi'] = datax['target_rsi']

    return data

def get_candle_body_range(date, num_days, data):
    """
    find candle body range over num_days
    """

    d = np.round(num_days/2, 0)
    i = data.index.get_loc(date)
    df_date = data.iloc[int(i-d):int(i+d+1), :]
    
    candle_body_high = max(df_date.Close.max(), df_date.Open.max())
    candle_body_low = min(df_date.Close.min(), df_date.Open.min())
    
    candle_body_range = [candle_body_high, candle_body_low]

    return candle_body_range

def get_double_bottoms(data):
    """
    find double bottom pattern
    """

    # Trim down to only 7 day lows
    df_7d_low = data[data['7d_low'].isin(['x'])].\
        reset_index(drop=False).copy()

    # Get column with next 7d_low for each 7d_low
    df_7d_low = get_next_day_cols(df_7d_low, ['date'])

    # Find valid double bottoms
    df_7d_low[['is_double_bottom', 'neck_max', 'db_day2']] =\
        df_7d_low.apply(lambda x: find_double_bottom(x.date, x.date_p1, data),
                        axis=1, result_type='expand')
    df_doub_bott =\
        df_7d_low[df_7d_low.is_double_bottom].copy().set_index('Date')
    
    data = data.merge(df_doub_bott[['is_double_bottom', 'neck_max', 'db_day2']],
                      how='left', left_index=True, right_index=True)

    data.is_double_bottom = data.is_double_bottom.fillna(False)

    return data

def get_break_pulls(data):
    """
    checks for a valid double bottom + break-through & pull-back
    """

    df_doub_bott = data[data.is_double_bottom].copy()

    df_doub_bott[['is_break_pull', 'date_entry']] =\
        df_doub_bott.apply(lambda x: find_break_pull(x.db_day2, x.neck_max, data),
                          axis=1, result_type='expand')
    
    data = data.merge(df_doub_bott[['is_break_pull', 'date_entry']],
                      how='left', left_index=True, right_index=True)

    data.is_break_pull = data.is_break_pull.fillna(False)

    return data
    
def find_double_bottom(date1, date2, data):
    """
    checks if a valid double bottom trend exists between two low price dates
    """

    day1 = data.set_index('date').loc[date1,:].to_dict()
    day2 = data.set_index('date').loc[date2,:].to_dict()
    i1 = data.index.get_loc(date1)
    i2 = data.index.get_loc(date2)

    band_high = min(day1['Open'], day1['Close'])
    band_low = day1['Low']

    # candle_body_low_1 = get_candle_body_range(date1, 5, df_day)[1]
    candle_body_low_2 = get_candle_body_range(date2, 5, data)[1]

    if date1 != date2 and day2['Low'] < band_high and\
        candle_body_low_2 > band_low and (i2 - i1) > 7:

        is_double_bottom = True
        i1 = data.index.get_loc(date1)
        i2 = data.index.get_loc(date2)
        neck_max =\
            data.set_index('date').iloc[int(i1+1):int(i2)].High.max()
        db_day2 = date2

    else:
        is_double_bottom = False
        neck_max = 0
        db_day2 = False

    return is_double_bottom, neck_max, db_day2

def find_break_pull(date, neck_max, data):
    """
    looks for a break-through, pull-back up trend
    """

    # Reset dataframe to start at low of 2nd double bottom
    dfx = data.loc[date:, :].copy()
    i_doub_bott = data.index.get_loc(date)
    doub_bott_low = dfx.iloc[0,:].Low
    
    is_break_pull = False
    date_trigger = False

    # Find when price breaks through double bottom neck
    dfx['break_margin'] = dfx.body_high - neck_max
    # dfx['break_margin'] = dfx.Low - neck_max
    if len(dfx[dfx['break_margin']>0]) != 0:
        date_break = dfx[dfx['break_margin']>0].index[0]
        dfx = data.loc[date_break:, :].copy()
        # dfx = data.loc[date_break:, :].iloc[1:,:].copy()
        i_break = data.index.get_loc(date_break)
        low_before_break = data.iloc[int(i_doub_bott+1):int(i_break)].Low.min()

        # Check if price dropped below double bottom low before breaking neck_max
        # Find next 5 day high
        if low_before_break > doub_bott_low and len(dfx[dfx['5d_high']=='x']) != 0:
            date_high = dfx[dfx['5d_high']=='x'].index[0]
            dfx = data.loc[date_high:, :].copy().iloc[2:,:]

            # Find first day where low is within 3% of neck_max
            dfx['neck_margin'] = np.absolute((dfx.Low-neck_max)/neck_max)
            if len(dfx[dfx.neck_margin < .03]) != 0:
                date_pullback = dfx[dfx.neck_margin < .03].index[0]
                dfx = data.loc[date_pullback:, :].copy()

                # Find first green candle at least 2 days after 5 day high
                if len(dfx[dfx.cdl_color == 'green']) != 0:
                    date_green = dfx[dfx.cdl_color == 'green'].index[0]
                    i_green = data.index.get_loc(date_green)
                    if len(data) > i_green + 1:
                        date_trigger = data.iloc[i_green+1,:].date
                        is_break_pull = True

    return is_break_pull, date_trigger
