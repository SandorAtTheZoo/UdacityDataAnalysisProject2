import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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
topMoneyGenres = dfMergedMoney.groupby(dfMergedMoney['genres']).size().sort_values(ascending=False).head(25)
#look at most popular directors for top money makers
print dfMergedMoney.groupby(dfMergedMoney['director']).size().sort_values(ascending=False).head()
#now look at actors in top money making movies
print dfMergedMoney.groupby(dfMergedMoney['cast']).size().sort_values(ascending=False).head()

###############by quality
qualityFields = ['id', 'vote_average', 'vote_count']
df_quality = pd.read_csv(filename, usecols=qualityFields)
#cast to float for possible division
df_quality[['vote_average', 'vote_count']] = df_quality[['vote_average', 'vote_count']].astype(float)
print df_quality[['vote_average', 'vote_count']].describe()
#since the standard deviation is greater than the mean, it is difficult to find meaning for review quality with few reviewers.  This makes sense, as the age of some of these movies would mean that they have less reviews.
#I'm going to ignore the number of reviews for this investigation
#standardize the average vote quality\
#The IQR at 50% is 38 votes, so let's make that the lower limit for ranking...it's not fair, but it should help eliminate artifically high scores due to few votes
#due to warnings...
#http://pandas.pydata.org/pandas-docs/stable/indexing.html#indexing-view-versus-copy
df_quality.loc[:, 'voteValStandardized']=((df_quality.loc[:, 'vote_average'] - df_quality.loc[:, 'vote_average'].mean()) / df_quality.loc[:, 'vote_average'].std(ddof=0))
print df_quality.sort_values('voteValStandardized', ascending=False).head()
df_qualityReviewNumbers = df_quality[df_quality['vote_count'] >= 38].head(500)
print df_qualityReviewNumbers.sort_values('voteValStandardized', ascending=False).head()
print len(df_qualityReviewNumbers)

#now analyze quality
dfMergedQuality = df_qualityReviewNumbers.merge(df_commonFields, on='id', how='inner')
topQualityGenres = dfMergedQuality.groupby(dfMergedQuality['genres']).size().sort_values(ascending=False).head(25)
#look at most popular directors for top quality
print dfMergedQuality.groupby(dfMergedQuality['director']).size().sort_values(ascending=False).head()
#now look at actors in top quality movies
print dfMergedQuality.groupby(dfMergedQuality['cast']).size().sort_values(ascending=False).head()


#################by popularity
popularFields = ['id','popularity']
dfPopularity = pd.read_csv(filename, usecols=popularFields)
#standardize popularity and rank
dfPopularity.loc[:,'popularityStandardized'] = (dfPopularity.loc[:,'popularity'] - dfPopularity.loc[:,'popularity'].mean())/dfPopularity.loc[:,'popularity'].std(ddof=0)
print dfPopularity.sort_values('popularityStandardized',ascending=False).head()
dfPopularityTop = dfPopularity.sort_values('popularityStandardized',ascending=False).head(500)
dfMergedPopularity = dfPopularityTop.merge(df_commonFields, on='id', how='inner')

topPopularGenres = dfMergedPopularity.groupby(dfMergedPopularity['genres']).size().sort_values(ascending=False).head(25)
#look at most popular directors for top quality
topPopularDirectors = dfMergedPopularity.groupby(dfMergedPopularity['director']).size().sort_values(ascending=False).head(10)
#now look at actors in top quality movies
topPopularCast = dfMergedPopularity.groupby(dfMergedPopularity['cast']).size().sort_values(ascending=False).head(10)

#find common genres across 3 measures of movies
popularGenreList = list(topPopularGenres.index)
intersectTemp = topPopularGenres.index.intersection(topMoneyGenres.index)
intersectGenres = intersectTemp.intersection(topQualityGenres.index)
print intersectGenres
#NOW MERGE ALL VALUES FOR THESE CATEGORIES
#create dataframes from all previous assemblies to do merge on indices

df_PopularGenres = pd.DataFrame(topPopularGenres,columns=['genres'])
df_QualityGenres = pd.DataFrame(topQualityGenres,columns=['genres'])
df_MoneyGenres = pd.DataFrame(topMoneyGenres,columns=['genres'])
# genreComparison = df_PopularGenres.merge(df_QualityGenres,on='genres',how='inner')

#THIS GUY!
#https://stackoverflow.com/questions/26366021/pandas-aligning-multiple-dataframes-with-timestamp-index
print df_PopularGenres.join(df_QualityGenres,how='inner',rsuffix='_1').join(df_MoneyGenres,how='inner',rsuffix='_2')


#print genreComparison

# print pd.concat([topPopularGenres,topMoneyGenres],axis=1).reset_index()
# testAlignL,testAlignR = topPopularGenres.align(topMoneyGenres,join='inner')
# comboAlign = pd.concat([testAlignL,testAlignR],axis=1)
# print comboAlign


#CREATE BARCHART OF GENRES FROM ALL 3 CATEGORIES
N=10 #the number of genre categories displayed
ind = np.arange(N) #x locations for the groups
width = 0.35

fig,ax = plt.subplots()
rects1 = ax.bar(ind, dfMergedMoney.groupby(dfMergedMoney['genres']).size().sort_values(ascending=False).head(10),width,color='r')

ax.set_ylabel('Movies of this genre')
ax.set_title('Top 5% of all movies by genre')
ax.set_xticks(ind+width/2)
ax.set_xticklabels(popularGenreList)
#https://stackoverflow.com/questions/10998621/rotate-axis-text-in-python-matplotlib
plt.xticks(rotation=90)
#https://stackoverflow.com/questions/6774086/why-is-my-xlabel-cut-off-in-my-matplotlib-plot
plt.gcf().subplots_adjust(bottom=0.5)

#ax.legend((rects1[0]),('Money','Quality','Popularity'))
plt.show()
#CREATE SCATTERPLOT OF POPULARITY VS MONEY -> RUN PEARSON'S R

#CREATE SCATTERPLOT OF POPULARITY VS QUALITY -> RUN PEARSON'S R

#CREATE SCATTERPLOT OF QUALITY VS MONEY -> RUN PEARSON'S R

