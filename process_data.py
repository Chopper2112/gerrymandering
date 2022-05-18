from msilib import type_valid
import scipy.stats
import numpy as np
import pandas as pd
import json
import math
import statistics as stats
import re

#####################################################################################

def notEnoughData(numElections): 
        print('WARNING: INSUFFICIENT NUMBER OF ELECTIONS ('+str(numElections)+') - IS '+year+' AN ELECTION YEAR?') 
        quit()

#####################################################################################

states = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "DC": "District Of Columbia",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming"}

# First array value is display name, second array value is label in input csv
houseName = {
    "VA": {
        "upper": ["State Senate", "State Senate"],
        "lower": ["House of Delegates", "House of Delegates"],
    },
    "PA": {
        "upper": ["State Senate", "STATE SENATE"],
        "lower": ["House of Representatives", "STATE HOUSE"],
    },
    "MD": {
        "upper": ["State Senate", "STATE SENATE"],
        "lower": ["House of Delegates", "STATE HOUSE"],
    }
}

index = {
    "vote": 3,
    "house": 1,
    "party": 2,
    "precinct": 0,
    "district": 4,
    "state": 5
}


#####################################################################################

def calcDistrictStats(districts):
    for d in districts:
        
        # Calculate total votes & voter turnout
        districts[d]["total_votes"] = districts[d]["Republican"] + districts[d]["Democratic"] + districts[d]["Other"]
        districts[d]["voter_turnout_%"] = round(districts[d]["total_votes"] / districts[d]["population"] * 100, 1)
        
        # Calculate winner
        if districts[d]["Republican"] > districts[d]["Democratic"]: 
            districts[d]["winner"] = "Republican"
        elif districts[d]["Republican"] < districts[d]["Democratic"]:
            districts[d]["winner"] = "Democratic"
        else: districts[d]["winner"] = "Other"
        
        # Calculate percentage of votes each party earned
        districts[d]["Republican_%"] = round(districts[d]["Republican"] / districts[d]["total_votes"] * 100, 2)
        districts[d]["Democratic_%"] = round(districts[d]["Democratic"] / districts[d]["total_votes"] * 100, 2)
        districts[d]["Other_%"] = round(districts[d]["Other"] / districts[d]["total_votes"] * 100, 2)
        
        # Calculate win margin
        districts[d]["win_margin"] = abs(districts[d]["Republican"] - districts[d]["Democratic"])
        try: districts[d]["win_margin_%"] = round(districts[d]["win_margin"] / (districts[d]["Republican"] + districts[d]["Democratic"]) * 100, 2) 
        except: pass
        
        # Warn if Other has majority
        if districts[d]["Other_%"] > 50: print('WARNING: District '+str(d)+' has a majority "Other" vote.')
    
    return districts

def calcNationalDistricts(precincts):

    districts_R = {}
    districts_D = {}
    for precinct in precincts:
        key = precinct[index["state"]]+str(precinct[index["district"]])

        # Republican votes
        if precinct[index["party"]] == 'REPUBLICAN':
            if key not in districts_R.keys(): 
                districts_R[key] = precinct[index["vote"]]
            else: districts_R[key] += precinct[index["vote"]]

        # Democrat votes
        elif precinct[index["party"]] == 'DEMOCRAT':
            if key not in districts_D.keys(): 
                districts_D[key] = precinct[index["vote"]]
            else: districts_D[key] += precinct[index["vote"]]
    
    return districts_R, districts_D


def calcNationalWinShares(votes_R, votes_D):

    winShares_R = []
    winShares_D = []

    # Iterate through each district
    for key in votes_R.keys():

        # Add winner's vote share to winner's array if both parties competed in the district
        if key in votes_D.keys():
            r = votes_R[key]
            d = votes_D[key]

            if r > d: winShares_R.append(min(75, r/(r+d)*100))
            if r < d: winShares_D.append(min(75, d/(r+d)*100))

    return winShares_R, winShares_D


def createChamber(districts, chamberName):
    
    # Cancel if there is no election data for this chamber
    if len(districts) == 0:
        print('\nWARNING: NO DATA FOR '+chamberName+' '+year)
        return
    
    # Create chamber dict
    chamber = {}
    chamber["metadata"] = {"state": stateName, "year": int(year), "chamber": chamberName}
    chamber["gerrymandering"] = {}
    chamber["seats"] = {"total": len(districts), "Republican": 0, "Democratic": 0}
    chamber["votes"] = {"total": 0, "Republican": 0, "Democratic": 0, "Other": 0, "Republican_%": 0, "Democratic_%": 0, "Other_%": 0}
    chamber["majority"] = "UNKNOWN"
    chamber["population"] = 0
    chamber["avg_population"] = 0
    chamber["voter_turnout_%"] = 0
    chamber["avg_win_margin"] = 0
    chamber["avg_win_margin_%"] = 0
    chamber["districts"] = districts

    # Calculate data
    for d in districts:
        
        # Number of seats for each party
        if districts[d]["winner"] == "Republican": chamber["seats"]["Republican"] += 1
        if districts[d]["winner"] == "Democratic": chamber["seats"]["Democratic"] += 1
    
        # Votes
        chamber["votes"]["Republican"] += districts[d]["Republican"]
        chamber["votes"]["Democratic"] += districts[d]["Democratic"]
        chamber["votes"]["Other"] += districts[d]["Other"]
        chamber["votes"]["total"] += districts[d]["total_votes"]
        
        # Votes %
        chamber["votes"]["Republican_%"] = round(chamber["votes"]["Republican"] / chamber["votes"]["total"] * 100, 1)
        chamber["votes"]["Democratic_%"] = round(chamber["votes"]["Democratic"] / chamber["votes"]["total"] * 100, 1)
        chamber["votes"]["Other_%"] = round(chamber["votes"]["Other"] / chamber["votes"]["total"] * 100, 2)
        
        # Majority
        if chamber["seats"]["Republican"] > chamber["seats"]["Democratic"]: chamber["majority"] = "Republican"
        elif chamber["seats"]["Republican"] < chamber["seats"]["Democratic"]: chamber["majority"] = "Democratic"
        else: chamber["majority"] = "SPLIT"
    
        # State population & ideal/average population per district
        chamber["population"] += districts[d]["population"]
        chamber["avg_population"] += round(districts[d]["population"] / chamber["seats"]["total"])
                     
        # Voter turnout
        chamber["voter_turnout_%"] = round(chamber["votes"]["total"] / chamber["population"] * 100, 1)
        
        
    # Average win margin
    chamber["avg_win_margin"] = round(abs(chamber["votes"]["Republican"] - chamber["votes"]["Democratic"]) / chamber["seats"]["total"])
    chamber["avg_win_margin_%"] = round((abs(chamber["votes"]["Republican"] - chamber["votes"]["Democratic"]) / (chamber["votes"]["Republican"]+chamber["votes"]["Democratic"])) * 100, 2)
  
    return chamber


#####################################################################################

# Main call
def calcGerrymandering(chamber):
    
    # Return if no districts
    if not chamber: return chamber
    
    # Conduct gerrymandering tests
    chamber["gerrymandering"]["test1"] = gerryTest1(chamber)
    chamber["gerrymandering"]["test2"] = gerryTest2(chamber)
    chamber["gerrymandering"]["test3"] = gerryTest3(chamber)

    majority = chamber["majority"]
    test1Score, test1Party = chamber["gerrymandering"]["test1"]["delta"], chamber["gerrymandering"]["test1"]["favored"]
    test2Score, test2Party = chamber["gerrymandering"]["test2"]["t_value"], chamber["gerrymandering"]["test2"]["favored"]
    test3Score, test3Party = chamber["gerrymandering"]["test3"]["delta"], chamber["gerrymandering"]["test3"]["favored"]

    # Calculate generalized gerrymandering score
    # gerryIndex = ["0","0","0"]
    # if test1Party == majority: gerryIndex[0] = "1"
    # if test2Party == majority: gerryIndex[1] = "1"
    # if test3Party == majority: gerryIndex[2] = "1"
    # chamber["gerrymandering"]["score"] = gerryIndex[0]+gerryIndex[1]+gerryIndex[2]

    gerryIndex = 0
    if test1Party == majority: gerryIndex += test1Score
    if test2Party == majority: gerryIndex += test2Score
    if test3Party == majority: gerryIndex += test3Score
    chamber["gerrymandering"]["score"] = gerryIndex

    # Return result of gerrymandering tests & export to JSON
    return chamber

# Simulated Seats vote
def gerryTest1(chamber):

    # Data
    winner = chamber["majority"]
    seats = chamber["seats"]["total"]
    winnerSeats = chamber["seats"][winner]
    votes = chamber["votes"]["total"]
    winnerVotes = chamber["votes"][winner]

    # Calculations
    expectedSeats = winnerVotes/votes * seats
    sigma = winnerVotes/votes * math.sqrt(seats)
    delta = (expectedSeats-winnerSeats) / sigma

    # Favored party
    favored = None
    if abs(delta) > 1: favored = winner

    # Return results
    return {
        "delta": delta,
        "expected_seats": expectedSeats,
        "favored": favored,
    }

# Lopsided Votes test (T-test)
def gerryTest2(chamber):
    win_shares_R = []
    win_shares_D = []

    # Iterate through each district
    for d in chamber["districts"]:
        winningParty = chamber["districts"][d]["winner"]
        vote_R = chamber["districts"][d]["Republican_%"]
        vote_D = chamber["districts"][d]["Democratic_%"]
        uncontested =  not (vote_R and vote_D)
        vote = max(vote_R,vote_D)*(1-uncontested) + 75*uncontested    # default to 75% if uncontested

        if(winningParty == "Republican"): win_shares_R.append(vote)
        if(winningParty == "Democratic"): win_shares_D.append(vote)

    # Calculate basic statistics
    try:
        var_R = stats.variance(win_shares_R)
        var_D = stats.variance(win_shares_D)
        mean_R = stats.mean(win_shares_R)
        mean_D = stats.mean(win_shares_D)
        n_R = len(win_shares_R)
        n_D = len(win_shares_D)
    except: notEnoughData(len(win_shares_R)+len(win_shares_D))

    # Calculate favored party
    if(mean_R < mean_D): favored = "Republican"
    if(mean_R > mean_D): favored = "Democratic"

    # Calculate T-Value
    df = n_R + n_D - 2
    pooledVar = ((n_R-1)*var_R+(n_D-1)*var_D)/(n_R+n_D-2)
    stdev = math.sqrt(pooledVar/n_R+pooledVar/n_D)
    tValue = abs(mean_D-mean_R)/stdev
    pValue = 1-scipy.stats.t.cdf(tValue, df)
    if pValue > .05: favored = None

    # Prepare data for JSON export
    return {
        "df": df,
        "t_value": tValue,
        "p_value": pValue,
        "Republican_win_mean": mean_R,
        "Democratic_win_mean": mean_D,
        "favored": favored,
    }

# Skewed Districts test
# NOTE: If swing state, use mean-median difference test. If one-party state, use chi-squared test.
def gerryTest3(chamber):
    includesUncontested = False

    if(chamber["votes"][chamber["majority"]+"_%"] >= 60):
        return gerryTest3_ChiSquare(chamber, includesUncontested, chamber["majority"])
    else:
        return gerryTest3_MeanMedDif(chamber, includesUncontested)

# Chi-squared test of comparing variances for states with one party rule
def gerryTest3_ChiSquare(chamber, includesUncontested, party):
    if(party == 'Republican'): nationalStdev = stats.stdev(winShares_R)
    if(party == 'Democratic'): nationalStdev = stats.stdev(winShares_D)
    
    win_shares = []
    districts = chamber["districts"]
    for d in range(1,len(districts)+1):
        if(districts[d]["winner"] == party) and (districts[d]["win_margin_%"] < 100 or includesUncontested): 
            win_shares.append(districts[d][party+"_%"]*(1-includesUncontested)+min(districts[d][party+"_%"], 75*includesUncontested))
  
    # Calculate chi-squared test variables
    stateStdev = stats.stdev(win_shares)
    sampleSize = len(win_shares)
    degFreedom = sampleSize-1

    # Calculate significance
    testStatistic = degFreedom*stateStdev/nationalStdev
    critValue = scipy.stats.chi2.isf(.05, degFreedom)
    delta = testStatistic/critValue

    # Set party as favored if significant result
    favored = None
    if(delta > 1): favored = party
    
    # Prepare data for JSON export
    return {
        "delta": delta, 
        "testStatistic": testStatistic,
        "critValue": critValue,
        "includesUncontested": includesUncontested,
        "favored": favored,
    }

# Mean median difference test for states with close elections
def gerryTest3_MeanMedDif(chamber, includesUncontested):
    win_shares_R = []
    districtCount = 0

    # Iterate through each district
    for d in chamber["districts"]:
        winningParty = chamber["districts"][d]["winner"]
        vote_R = chamber["districts"][d]["Republican_%"]
        vote_D = chamber["districts"][d]["Democratic_%"]
        uncontested = not (vote_R and vote_D)
        if uncontested and not includesUncontested: continue
        vote = max(vote_R,vote_D)*(1-uncontested) + 75*uncontested  # default to 75% if uncontested

        if(winningParty == "Republican"): win_shares_R.append(vote)
        districtCount += 1

    # Calculate basic statistics
    try:
        mean = stats.mean(win_shares_R)
        median = stats.median(win_shares_R)
        stdev = stats.stdev(win_shares_R)

        sigma = 0.756*stdev/math.sqrt(districtCount)
        meanMedDif = mean - median
        delta = meanMedDif/sigma
    except: notEnoughData(len(win_shares_R))
    # print(win_shares_R)
    # print(includesUncontested, districtCount, mean, median, stdev, sigma, meanMedDif, delta)

    # Calculate favored party
    if(delta < 0): favored = "Republican"
    if(delta > 0): favored = "Democratic"
    if(abs(delta) < 2): favored = None

    # Prepare data for JSON export
    return {
        "delta": delta, 
        "sigma": sigma,
        "meanMedDif": meanMedDif,
        "includesUncontested": includesUncontested,
        "favored": favored,
    }


#####################################################################################

# Get inputs from user
stateAcronym = input('State Acronym: ').upper()
stateName = states[stateAcronym]
year = input('Year: ')
print((stateName+" "+year+"\n").upper())

# Get data from files
electionDataRaw = pd.read_csv('input/'+stateAcronym+'/'+stateName.upper()+' '+year+' Precincts.csv', sep=',')
nationalDataRaw = pd.read_csv('input/National/NATIONAL '+year+' Precincts.csv', sep=',')
populationData = json.load(open('input/'+stateAcronym+'/Population.json'))

# Convert to numpy and get indices
nationalData = nationalDataRaw.to_numpy()
electionData = electionDataRaw.to_numpy()


# Clean data
for i in range(len(electionData)): 
    electionData[i,index["vote"]] = int(math.floor(float(str(electionData[i,index["vote"]]).replace(',','').replace('nan','0'))))
    electionData[i,index["district"]] = re.sub("[^0-9]", "", str(electionData[i,index["district"]]))
    if electionData[i,index["district"]]: electionData[i,index["district"]] = int(electionData[i,index["district"]])

# Remove data that is not useful and sort by district
electionData = np.delete(electionData, np.where(electionData[:,index["vote"]]<=0)[0], 0)
electionData = np.delete(electionData, np.where((np.logical_and(electionData[:,index["house"]]!=houseName[stateAcronym]['upper'][1], electionData[:,index["house"]]!=houseName[stateAcronym]['lower'][1])))[0], 0)
electionData = electionData[np.argsort(electionData[:, index["district"]].astype(int))]

# Record stats by district in each house
upper_districts = {}
lower_districts = {}
for candidate in electionData:
    
    # Get information for each candidate
    votes = int(candidate[index["vote"]])
    party = candidate[index["party"]]
    house = candidate[index["house"]]
    district = int(candidate[index["district"]])
    
    # Other parties
    if "REP" in party.upper(): party = "Republican"
    if "DEM" in party.upper(): party = "Democratic"
    if party != "Republican" and party != "Democratic": party = "Other"
    
    # Add up votes & other statistics
    try:
        if house == houseName[stateAcronym]['upper'][1]:
            if district not in upper_districts.keys():
                upper_districts[district] = {"Republican": 0, "Democratic": 0, "Other": 0, "population": populationData[houseName[stateAcronym]["upper"][0]][str(district)]}
            upper_districts[district][party] += votes

        elif house == houseName[stateAcronym]['lower'][1]:
            if district not in lower_districts.keys():
                lower_districts[district] = {"Republican": 0, "Democratic": 0, "Other": 0, "population": populationData[houseName[stateAcronym]["lower"][0]][str(district)]}
            lower_districts[district][party] += votes
    except: print('ERROR adding votes. Does the Population data use the correct chamber names?')
        
    
# Calculate various statistics for each district in both houses
upper_districts = calcDistrictStats(upper_districts)
lower_districts = calcDistrictStats(lower_districts)

# Create dicts and calculate stats for whole chamber
state_lower = createChamber(lower_districts, houseName[stateAcronym]['lower'][0])
state_upper = createChamber(upper_districts, houseName[stateAcronym]['upper'][0])

# Process national data
nationalVotes_R, nationalVotes_D = calcNationalDistricts(nationalData)
winShares_R, winShares_D = calcNationalWinShares(nationalVotes_R, nationalVotes_D)

# Calculate gerrymandering
state_lower = calcGerrymandering(state_lower)
state_upper = calcGerrymandering(state_upper)

# Fetch registered voter count
# state_upper["registered_voters"] = populationData["registered_voters"]
# state_lower["registered_voters"] = populationData["registered_voters"]

# Print out data for debugging
# for i in range(1,len(state_upper['districts'])+1):
    # print(str(i), state_upper['districts'][i]['winner'], state_upper['districts'][i]['win_margin_%'])
    
# Output to JSON files
print()
if state_upper:
    with open('output/'+stateAcronym+'/'+year+'_Upper.json', 'w') as outputFile:
        json.dump(state_upper, outputFile, indent=4)
        print('Exported '+'output/'+stateAcronym+'/'+year+'_Upper.json')

if state_lower:    
    with open('output/'+stateAcronym+'/'+year+'_Lower.json', 'w') as outputFile:
        json.dump(state_lower, outputFile, indent=4)
        print('Exported '+'output/'+stateAcronym+'/'+year+'_Lower.json')
print()