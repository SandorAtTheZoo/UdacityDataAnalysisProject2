import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
filename = 'tmdb-movies.csv'
dfMovies = pd.read_csv(filename)
#print dfMovies.head()

independentFields = ['id','budget','cast','director','genres']
df_commonFields = pd.read_csv(filename,usecols=independentFields)
#print df_commonFields.head()

moneyFields = ['id','budget','revenue']
df_movieMoney = pd.read_csv(filename, usecols=moneyFields)
#convert money fields to float64 for division
#https://stackoverflow.com/questions/15891038/change-data-type-of-columns-in-pandas
df_movieMoney[['budget','revenue']] = df_movieMoney[['budget','revenue']].astype(float)
#now try to change genres to sets to get better groupby performance
df_commonFields['genres'] = df_commonFields.apply(lambda row: set(row['genres']),axis=1)
#print df_movieMoney.head()

def rankByMoney(df):
    if (df['revenue'] > 1) and (df['budget'] > 100000):
        return (df['revenue'] - df['budget']) / df['budget']
    else:
        return -100

#using sort_values due to this timing experiment :
#https://stackoverflow.com/questions/41825978/sorting-columns-and-selecting-top-n-rows-in-each-group-pandas-dataframe
df_movieMoney['moneyRank'] = df_movieMoney.apply(rankByMoney, axis=1).sort_values(ascending = False)

#print df_movieMoney.sort_values(by=['moneyRank'],ascending=False).head()

#now get top 500 moneyRanked movies and look for common directors
df_topMovieMoney = df_movieMoney.sort_values(by=['moneyRank'],ascending=False).head(500)
#print df_commonFields.head()
dfMerged = df_topMovieMoney.merge(df_commonFields,on='id',how='inner',suffixes=('','_'))
#now fix merge
#https://stackoverflow.com/questions/40343061/duplicate-columns-with-pandas-merge
dfMerged.drop('budget_',axis=1,inplace=True)
print dfMerged.head()
#print df_commonFields.head()
#print df_commonFields[df_commonFields['id'] == 76341]

print len(dfMerged)

print df_topMovieMoney.columns
print df_commonFields.columns

print dfMerged.groupby(dfMerged['director']).groups
#playing around with list of genre ranking
#https://stackoverflow.com/questions/19384532/how-to-count-number-of-rows-in-a-group-in-pandas-group-by-object
print dfMerged.groupby(dfMerged['genres']).size().sort_values(ascending=False)