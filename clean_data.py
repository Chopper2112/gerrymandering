import pandas as pd
import numpy as np

path = 'C:\\Users\\815820\\OneDrive - Loudoun County Public Schools\\Desktop\\Sr Project\\input\\National\\'
state = input('Nationwide Elections Dataset Cleaner\n\nClean Type ("national" or state name): ').upper()
year = input('Year: ')

columns = ['precinct','office','party_simplified','votes','district','state']
cols_to_use = (0,1,2,3,4,5)
if state == "NATIONAL": cols_to_use = (0,1,3,5,11,16)   # use if creating national cleaned data from the raw download

dataRaw = pd.read_csv(path+'NATIONAL '+year+' Precincts.csv', sep=',', usecols=cols_to_use)
data = dataRaw.to_numpy()

# Clean data
data = data[(np.logical_or(data[:,1] == "STATE HOUSE", data[:,1] == "STATE SENATE"))] # office
data = data[(np.logical_or(data[:,2] == "DEMOCRAT", data[:,2] == "REPUBLICAN"))] # party
data = data[data[:,3].astype(int) > 0] # votes
if state != "NATIONAL": data = data[data[:,5] == state] # state
for row in data:
    if ',' in str(row[0]): row[0] = str(row[0]).replace(',','')
    if ',' in str(row[4]): row[4] = str(row[4]).replace(',','')

# Export
np.savetxt(path+state+" "+year+" Precincts.csv", data, delimiter=",", fmt='%s')
print('Done.')