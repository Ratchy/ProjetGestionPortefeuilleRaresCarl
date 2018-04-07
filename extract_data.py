import os
import numpy as np
import pandas as pd
import pickle
import quandl
from datetime import datetime
import matplotlib.pyplot as plt
import math
import random
from datetime import datetime, date, timedelta

#la fonction globale du script
def extract(): 
    ################################################################## On définit les fonctions ########################################
     
    def get_json_data(json_url, cache_path):
        '''Download and cache JSON data, return as a dataframe.'''
        try:        
            f = open(cache_path, 'rb')
            df = pickle.load(f)   
            print('Loaded {} from cache'.format(json_url))
        except (OSError, IOError) as e:
            print('Downloading {}'.format(json_url))
            df = pd.read_json(json_url)
            df.to_pickle(cache_path)
            print('Cached {} at {}'.format(json_url, cache_path))
        return df
     
    def get_crypto_data(poloniex_pair):
        '''Retrieve cryptocurrency data from poloniex'''
        json_url = base_polo_url.format(poloniex_pair, start_date.timestamp(), end_date.timestamp(), pediod)
        data_df = get_json_data(json_url, folder+poloniex_pair)
        data_df = data_df.set_index('date')
        return data_df
     
     
    def merge_dfs_on_column(dataframes, labels, col):
        '''Merge a single column of each dataframe into a new combined dataframe'''
        series_dict = {}
        altcoins_list = []
        for index in range(len(dataframes)):
            if len(dataframes[index]["close"]) > min_lenght:
                series_dict[labels[index]] = dataframes[index][col]
                altcoins_list.extend([labels[index]])
             
        return pd.DataFrame(series_dict)
      
     
     
     
    def choose_timeframe(pediod):
        if pediod == 300:
            folder = "5_minn/"
            min_lenght = 210000
     
        if pediod == 900:
            folder = "15_min/"
            min_lenght = 70000
     
        if pediod == 1800:
            folder = "30_min/"
            min_lenght = 35000
     
        if pediod == 7200:
            folder = "2_h/"
            min_lenght = 8750
         
        if pediod == 14400:
            folder = "4_h/"
            min_lenght = 4375
             
        if pediod == 86400:
            folder = "1_j/"
            min_lenght = 729
     
        return folder, min_lenght
     
    def alcoin_extract_from_poloniex(altcoins):
        altcoin_data = {}
        for altcoin in altcoins:
            coinpair = 'BTC_{}'.format(altcoin)
            crypto_price_df = get_crypto_data(coinpair)
            altcoin_data[altcoin] = crypto_price_df
     
        return altcoin_data
       
    ################################################# On définit les variables ##################################################
    ##Variables pour downloader
    base_polo_url = 'https://poloniex.com/public?command=returnChartData&currencyPair={}&start={}&end={}&period={}'
    start_date = datetime.strptime('2016-02-17 00:00:00', '%Y-%m-%d %H:%M:%S')
    end_date = datetime.now()
    pediod = 300 # 300 sec, donc 5 min d'échart entre les valeurs
    altcoins = ["ETH","XRP","LTC","XMR","LSK","STR","XEM","ETC","BCH","ZEC","BTS",
                "ZRX","STRAT","OMG","DGB","VTC","GAME","DCR","PPC",
                "REP","GNT","EMC2","FCT","MAID","SYS","ARDR","STEEM","CVC","VIA"]
    altcoins = ["ETH","XRP","LTC","XMR","LSK","STR","XEM","ETC","BCH","ZEC","BTS",
            "ZRX","STRAT","OMG","DGB","VTC","GAME","DCR","PPC",
            "REP","GNT","EMC2","FCT","MAID","SYS","ARDR","STEEM","CVC","VIA",
            "VRC","EXP","GAS","LBC","BURST","PASC","XCP","STORJ","GNO","NAV","CLAM",
            "POT","AMP","OMNI","BLK","XVC","RADS","NXC","GRC","FLO","BELA","BTM",
            "PINK","RIC","XBC","SBD","BCY","FLDC","HUC","NEOS"]

    #################################################Le code pour extraire le data############################################


    folder, min_lenght = choose_timeframe(pediod)

    altcoin_data = alcoin_extract_from_poloniex(altcoins)

    combined_df = merge_dfs_on_column(list(altcoin_data.values()), list(altcoin_data.keys()), 'close')

    return combined_df
