# imports ...
from utils import *
import pandas as pd

# user query entry point 
query=input("Greeting leader..Please specify the L2 board for which the feature readiness report is required.[APS,DIS,TES] : ")

# GuardRail
if query not in ["APS", "DIS", "TES"]:
    print("Invalid input. Please enter the one of the following options: APS, DIS, TES")

# JIRA API query here ..rsult json file stored in data/result.json
get_board_features(query)

# convert the aquired json to csv here and stored in data/API.csv
json_to_csv()

# loading the csv file  
df=pd.read_csv()

# parameters to check for 











