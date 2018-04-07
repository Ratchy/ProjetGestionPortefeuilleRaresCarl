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
import extract_data



################################################# On définit les fonctions ###############################################

def compute_individual_currency_profit(combined_df):
    tot_return = 0
    for altcoin in combined_df:
        print("Revenu pour la stratégie buy and hold sans marge pour %s: %s" %(altcoin, combined_df[altcoin][105120]/combined_df[altcoin][0]))
        tot_return += combined_df[altcoin][105120]/combined_df[altcoin][0]
    tot_return = tot_return/len(combined_df.columns)
    print("compute_individual_currency_profit")
    return tot_return

def make_graph_data(combined_df, temps, montant_initial, leverage):
    base_liste = []
    base_liste_2 = []
    combined_df = combined_df.values
    for x in range(0,105121, temps):
        punctual_price = 0
        for altcoin in range(len(combined_df[0])):
            punctual_price += montant_initial*(combined_df[x,altcoin]/combined_df[0,altcoin])
        punctual_price = punctual_price/len(combined_df[0])
        base_liste.extend([punctual_price*leverage])
        base_liste_2.extend([punctual_price])
    base_liste =base_liste[1:]
    base_liste_2 =base_liste_2[1:]

    return base_liste, base_liste_2


################################################# On définit les variables ###############################################

montant_initial = 0.2 # en BTC (investissement initial)

#Le nombre de périodes est le nombre de fois qu'on rééquilibre le portfolio. Le temps représente la durée de chaque période. Le total est de 1 an

#Voici les possibilités: temps*total_periods: 105120*1, 8760*12, 2022*52, 4043*26, 288*365, 12*8760, 6*17520,3*35040, 1*105120
temps =  6 #nombre de chandelles par période
total_periods = 17520 # nombre de périodes


leverage = 1 # la marge utilisée

minimum_transaction_size = 0.0002 #profits ou pertes minimaux pour faire une transaction. Ne peut être en dessous de 0.0001 car c'est le minimum sur poloniex.

sell_fees = 0.0015 #ça reste constant
buy_fees = 0.0025 #ça reste constant
spread = 0.004 #ça varie d'une crypto à l'autre. Il faudra en prendre compte car c'est gros et ça s'applique à l'achat et à la vente. Ça peut aller de 0.001 à 0.01.
                #plus c'est gros et plus ça fait mal, surtout qu'on trade très souvent. Plus c'est petit et plus on peut faire du high frequency trading (ex: 5 min)
                #plus c'est gros, moins on peut faire du high frequency trading (ex: 30 min, 1 hr)


################################################# On execute le code ###############################################
sell_fees = 1/(1+sell_fees)
buy_fees = 1/(1+buy_fees)
spread = 1/(1+spread)

df_list = []
altcoins_list = []


#ici on retire les prix des cryptos séléctionnées dans le script "extract_data" à partir de Poloniex
combined_df = extract_data.extract()

#on choisis l'année 2017 à aujourd'hui pour les données
combined_df = combined_df[:]['2017-03-22 00:00:00':'2018-03-23 00:00:00']


#ici on calcule le revenu individuel de chaque crypto si on aurait fait du buy and hold. On calcule aussi le revenu total qui est représenté par "tot_return".
#Cette donnée sert à comparer le profit de notre stratégie au profit d'une stratégie buy an hold.
tot_return = compute_individual_currency_profit(combined_df)


#Ici on prépare les listes qui seront utilisées pour faire la représentation graphique de la stratégie buy and hold et de la stratégie avec buy and hold + marge.
base_liste, base_liste_2 = make_graph_data(combined_df, temps, montant_initial, leverage)


plott =[]
total_pot = montant_initial
array = combined_df.values
too_little_transaction = 0


##Ici on applique la stratégie de gestion du portfolio. À chaque période, on redistribue également l'argent entre les crypto-monnaies. À chaque fois, on ne
## vend pas tout. On ne vend que le profit. Sinon, les frais de transaction sont trop grands.

liste = []
for altcoin in combined_df:
    liste.extend([total_pot/len(combined_df.columns)])
liste.extend([0])


for time in range(total_periods): #pour chaque période


    ##ici on calcule le revenu individuel pour chaque crypto-monnaie pour chaque période.
    for index in range(len(array[0])): #pour chaque crypto du portfolio
        montant = liste[index] # on calcule le montant qui lui sera accordé au début de chaque période
        montant_init = montant
        for i in range(1,temps+1): # pour chaque valeur du prix de la cryptomonnaie
            montant = montant*(array[i+time*temps][index]/array[i+time*temps-1][index]) # on calcule le revenu
        montant = montant_init*(((montant/montant_init)-1)*leverage+1) #on calcule le montant à la fin de la période en tenant compte de la marge utilisée aussi.

        if montant < 0.0000: #si la valeur a descendue en bas du prix de la transction minimale, on considère qu'on a tout perdu pour cette crypto
            print("destroyed")
            montant = 0
            
        liste[index] = montant #on ajoute la valeur à la fin de la période pour chaque crypto.

    #/(len(liste)-1)
    mean = sum(liste)/(len(liste)-1)# on calcule la moyenne des valeurs pour chaque crypto.

    
    ##ici on redistribue l'argent également entre chaque crypto du portfolio
    
    plus = 0 #"plus" correspond à la somme des profits additionnées à l'argent dans le compte qui n'est pas placé (liste[-1]).
    minus = 0 #"minus" correspond à la somme de pertes.
    
    for value in range(len(liste)-1): #chaque crypto de notre portfolio:
        if liste[value] > mean: #si la crypto a fait des profits dans la période:
            if ((liste[value] - mean)*sell_fees*spread) < minimum_transaction_size: # si le revenu est en bas de la transaction minimale
                too_little_transaction+=1 #on ajoute ça aux stats.
            if ((liste[value] - mean)*sell_fees*spread) >= minimum_transaction_size: # si le revenu est en haut de la transaction minimale
                plus += (liste[value] - mean)*sell_fees*spread #on vend en BTC. On prend en compte les fees et le spread

                
        if liste[value] < mean: #si la crypto a fait des pertes dans la période:
            if (mean - liste[value])*buy_fees*spread < minimum_transaction_size: # si la valeur absolue de pertes est en bas de la transaction minimale
                too_little_transaction+=1 #on ajoute ça aux stats.

    plus += liste[-1] # on contabilise aussi l'argent q'on a déjà dans le compte et qui n'est pas utilisé.

    for value in range(len(liste)-1): #chaque crypto de notre portfolio:
        if liste[value] > mean: #si la crypto a fait des profits dans la période:
            if ((liste[value] - mean)*sell_fees*spread) >= minimum_transaction_size: # si le revenu est en haut de la transaction minimale
                liste[value] = mean #on vend jusqu'à ce que le montant alloué à cette crypto soit égal à la moyenne du portfolio

        if liste[value] < mean: #si la crypto a fait des pertes dans la période:
            if ((mean - liste[value])*buy_fees*spread) >= minimum_transaction_size: # si la valeur absolue de pertes est en haut de la transaction minimale
                if (plus*buy_fees*spread) >= (mean - liste[value]): #s'il reste encore assez d'argent en BTC dans le compte pour acheter de la crypto
                    plus += ((liste[value] - mean)/(buy_fees*spread)) # on soustrait la valeur de l'achat à l'argent en BTC de notre compte
                    liste[value] = mean #on achète jusqu'à ce que le montant alloué à cette crypto soit égal à la moyenne du portfolio

    liste[-1] = plus #s'il reste de l'argent en BTC qu'on n'a pas pu distribuer dans les cryptos
    total_pot = sum(liste) # on calcule la valeur totale de notre portfolio
    plott.extend([total_pot]) # on ajoute le tout au graphique

print("Nombre de fois que le profit ou la perte a été en dessous de la transaction minimale: ", too_little_transaction)
print("Revenu total pour la stratégie de gestion du portfolio: ", int((total_pot/montant_initial)*100),"%")
print("On a battu le marché (avec marge) par : ",int(((total_pot/montant_initial)/(tot_return*leverage))*100),"%")
print("On a battu le marché (sans marge) par: ",int(((total_pot/montant_initial)/(tot_return))*100),"%")
plt.plot(plott, label = "Stratégie")
plt.plot(base_liste, label = "Buy and hold avec marge")
plt.plot(base_liste_2, label = "Buy and hold sans marge")
plt.legend(bbox_to_anchor=(1, 1), loc=2, borderaxespad=0.)
plt.show()







