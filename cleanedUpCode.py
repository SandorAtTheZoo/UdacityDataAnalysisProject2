import numpy as np
import pandas as pd

filename = 'tmdb-movies.csv'

independentFields = ['id','budget','cast','director','genres']
df_commonFields = pd.read_csv(filename,usecols=independentFields)


#define function to take in dataframe of independent fields and groom it to support groupby functions
listOfColumns = ['genres','cast','director']
#need to convert from set to tuple b/c groupby can't work on mutable objects
#https://stackoverflow.com/questions/39622884/pandas-groupby-over-list
def groomIndependentVars(df, colList):
    def setToTuple(x):
        return tuple(sorted(x))
    for column in colList:
        df[column] = df[column].astype(str)
        df[column] = df[column].str.split(pat='|')
        df[column] = df[column].apply(set)
        df[column] = df[column].apply(setToTuple)
    return df

df_commonFields = groomIndependentVars(df_commonFields,listOfColumns)

#now lay out how data is analyzed
################by money :
moneyFields = ['id','budget','revenue']
df_movieMoney = pd.read_csv(filename, usecols=moneyFields)
#prep money fields to float for division
#https://stackoverflow.com/questions/15891038/change-data-type-of-columns-in-pandas
df_movieMoney[['budget','revenue']] = df_movieMoney[['budget','revenue']].astype(float)

def rankByMoney(df):
    if (df['revenue'] > 1) and (df['budget'] > 100000):
        return (df['revenue'] - df['budget']) / df['budget']
    else:
        return -100

#using sort_values due to this timing experiment :
#https://stackoverflow.com/questions/41825978/sorting-columns-and-selecting-top-n-rows-in-each-group-pandas-dataframe
df_movieMoney['moneyRank'] = df_movieMoney.apply(rankByMoney, axis=1).sort_values(ascending = False)

#now get top 500 moneyRanked movies and look for common directors
df_topMovieMoney = df_movieMoney.sort_values(by=['moneyRank'],ascending=False).head(500)

dfMergedMoney = df_topMovieMoney.merge(df_commonFields, on='id', how='inner', suffixes=('', '_'))
#now fix merge
#https://stackoverflow.com/questions/40343061/duplicate-columns-with-pandas-merge
dfMergedMoney.drop('budget_', axis=1, inplace=True)

#look at most popular genres for top money makers
print dfMergedMoney.groupby(dfMergedMoney['genres']).size().sort_values(ascending=False).head()
#look at most popular directors for top money makers
print dfMergedMoney.groupby(dfMergedMoney['director']).size().sort_values(ascending=False).head()
#now look at actors in top money making movies
print dfMergedMoney.groupby(dfMergedMoney['cast']).size().sort_values(ascending=False).head()

###############by quality
qualityFields = ['id', 'vote_average', 'vote_count']
df_popular = pd.read_csv(filename, usecols=qualityFields)
#cast to float for possible division
df_popular[['vote_average','vote_count']] = df_popular[['vote_average','vote_count']].astype(float)
print df_popular[['vote_average','vote_count']].describe()
#since the standard deviation is greater than the mean, it is difficult to find meaning for review quality with few reviewers.  This makes sense, as the age of some of these movies would mean that they have less reviews.
#I'm going to ignore the number of reviews for this investigation
#standardize the average vote quality\
#The IQR at 50% is 38 votes, so let's make that the lower limit for ranking...it's not fair, but it should help eliminate artifically high scores due to few votes
#due to warnings...
#http://pandas.pydata.org/pandas-docs/stable/indexing.html#indexing-view-versus-copy
df_popular.loc[:,'voteValStandardized']=((df_popular.loc[:,'vote_average'] - df_popular.loc[:,'vote_average'].mean())/df_popular.loc[:,'vote_average'].std(ddof=0))
print df_popular.sort_values('voteValStandardized',ascending=False).head()
df_popularReviewNumbers = df_popular[df_popular['vote_count']>=38].head(500)
print df_popularReviewNumbers.sort_values('voteValStandardized',ascending=False).head()
print len(df_popularReviewNumbers)

#now analyze quality
dfMergedQuality = df_popularReviewNumbers.merge(df_commonFields, on='id',how='inner')
print dfMergedQuality.groupby(dfMergedQuality['genres']).size().sort_values(ascending=False).head()
#look at most popular directors for top quality
print dfMergedQuality.groupby(dfMergedQuality['director']).size().sort_values(ascending=False).head()
#now look at actors in top quality movies
print dfMergedQuality.groupby(dfMergedQuality['cast']).size().sort_values(ascending=False).head()


#################by popularity
