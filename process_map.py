import geojson
import numpy as np
import pandas as pd
import random
import math


# Variables
districts = 40
sizeAllowance = .05
optimalDistrictSize = 8631394/districts
minDistrictSize = optimalDistrictSize*(1-sizeAllowance)
maxDistrictSize = optimalDistrictSize*(1+sizeAllowance)
geoFile = 'Virginia_Geo_2020.json'
popFile = 'Virginia Race Pop 2020.csv'



# Load geodata
with open(geoFile) as f:
    gj = geojson.load(f)
features = gj['features']

# Load population data
popData = pd.read_csv(popFile, sep=',', usecols=(0,1,2), skiprows=1).to_numpy()



# Functions

def list_split(listA, n):
# https://appdividend.com/2021/06/15/how-to-split-list-in-python/#:~:text=To%20split%20a%20list%20into%20n%20parts%20in%20Python%2C%20use,array%20into%20multiple%20sub%2Darrays.
    for x in range(0, len(listA), n):
        every_chunk = listA[x: n+x]

        if len(every_chunk) < n:
            every_chunk = every_chunk + \
                [None for y in range(n-len(every_chunk))]
        yield every_chunk

def addPoint(name, coordinates):
    features.append({"type":"Feature","properties":{"NAME":name},"geometry":{"type":"Point","coordinates":[coordinates[0],coordinates[1]]}})

def calcDistance(coordinates1, coordinates2):
    return math.sqrt(math.pow((coordinates1[0]-coordinates2[0]),2)+math.pow((coordinates1[1]-coordinates2[1]),2))



# Compile data for each subdivision
for i, feature in enumerate(features):
    if(feature["geometry"]["type"]=="Point"): continue
    for popEntry in popData:

        # Add population value
        if(popEntry[0] == "0600000US"+feature["properties"]["GEOID"]): 
            feature["properties"]["POP"] = popEntry[2]

        # Internal points
        feature["properties"]["INTPTLAT"] = float(feature["properties"]["INTPTLAT"])
        feature["properties"]["INTPTLON"] = float(feature["properties"]["INTPTLON"])

        # ID
        feature["properties"]["ID"] = i+1

        # Origin  & District
        feature["properties"]["ORIGIN"] = False
        feature["properties"]["DISTRICT"] = 0

        # Color
        feature["properties"]["COLOR"] = None

    # Print subdivision data
    print(feature["properties"]["NAME"], "\t"*(len(feature["properties"]["NAME"])<8), feature["properties"]["POP"], feature["properties"]["INTPTLAT"], feature["properties"]["INTPTLON"], sep='\t')


# Choose origin subdivisions
tries = 0
originCount = 0
origins = []
candidateSubdivisions = features.copy() # subdivisions that have not been made an origin

# Iterate until necessary number of origins found
while len(origins) < districts:
    tries += 1
    randIndex = random.randint(0,len(candidateSubdivisions)-1) 
    subdivision = candidateSubdivisions[randIndex]
    try: subdivisionCoords = (subdivision["properties"]["INTPTLON"], subdivision["properties"]["INTPTLAT"])
    except: continue

    # Reject origin if too close to other origin
    goodOrigin = True
    for origin in origins:
        originCoords = (origin["properties"]["INTPTLON"], origin["properties"]["INTPTLAT"])
        if calcDistance(originCoords,subdivisionCoords) < 100/tries or subdivision["properties"]["POP"] < optimalDistrictSize*.28:
            goodOrigin = False

    # Accept origin
    if goodOrigin:
        # Set district
        subdivision["properties"]["ORIGIN"] = True
        subdivision["properties"]["DISTRICT"] = len(origins)+1
        subdivision["properties"]["DISTRICT_POP"] = subdivision["properties"]["POP"]

        # Set color
        r = lambda: random.randint(0,255)
        subdivision["properties"]["COLOR"] = '#%02X%02X%02X' % (r(),r(),r())

        # Add to origin list and remove from candidates
        origins.append(subdivision)
        candidateSubdivisions.pop(randIndex)




# Expand districts from origin
districtSizes = []
optimization = .0001

for i, origin in enumerate(origins):
    tries = 0
    originCenter = (origin["properties"]["INTPTLON"], origin["properties"]["INTPTLAT"])

    # Iterate through random candidates as long as population size is insufficient
    while origin["properties"]["DISTRICT_POP"] < minDistrictSize:
        
        # Increment tries (to broaden search)
        tries += 1
        if optimization*tries >= 5: break

        # Check random candidate
        try: randIndex = random.randint(0,len(candidateSubdivisions)-1)
        except: break
        candidate = candidateSubdivisions[randIndex]
        candidateCenter = (candidate["properties"]["INTPTLON"], candidate["properties"]["INTPTLAT"])

        # Check distance between origin and candidate and add if population will not exceed maximum
        distance = calcDistance(originCenter,candidateCenter)
        print(str(origin["properties"]["DISTRICT"])+"/"+str(districts), "p="+str(origin["properties"]["DISTRICT_POP"]), "d="+str(calcDistance(originCenter,candidateCenter)), "t="+str(tries), "cand="+str(len(candidateSubdivisions)), sep='\t')

        if distance < optimization*tries and (candidate["properties"]["DISTRICT"]+candidate["properties"]["POP"]) < maxDistrictSize:

            # Add candidate to district
            candidate["properties"]["DISTRICT"] = origin["properties"]["DISTRICT"]
            candidate["properties"]["COLOR"] = origin["properties"]["COLOR"]
            origin["properties"]["DISTRICT_POP"] += candidate["properties"]["POP"]
            candidateSubdivisions.pop(randIndex)
            if len(candidateSubdivisions) == 0: break








# Export to geojson file
if(input('\nExport? Y/N: ').upper() == 'Y'):
    with open(geoFile, 'w') as outputFile:
        outputFile.write('{"type":"FeatureCollection", "features": [\n')
        for i, feature in enumerate(features):
            outputFile.write(str(feature).replace(' ','').replace('\'','"'))
            if(i+1<len(features)): outputFile.write(",\n")
        outputFile.write("]}")
        print('Done.')