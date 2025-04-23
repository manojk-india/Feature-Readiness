# imports ...
from utils import *
# import pandas as pd

# user query entry point 
# query=input("Greeting leader..Please specify the L2 board for which the feature readiness report is required.[APS,DIS,TES] : ")

# GuardRail
# if query not in ["APS", "DIS", "TES"]:
#     print("Invalid input. Please enter the one of the following options: APS, DIS, TES")

# # JIRA API query here ..rsult json file stored in data/result.json
# get_board_features(query)

# # convert the aquired json to csv here and stored in data/API.csv
# json_to_csv()

# # now checking acceptance_crieteria and summary and suggesting better changes and ading those to csv file itself 
# process_evaluations()

# Now we have to check parameters
missing_value=count_empty_values("data/API.csv")

# This creates a dashboard with any parameters we give == only concebtrating for missing values
create_missing_values_dashboard(missing_value)

# Now worrying abt the quality of data == OverDue features , not so good Acceptance crieteria , Not so good summaries
# overdue Task number returned and csv saved in overdue.csv
no_of_over_due_features=save_overdue_tasks()

# No of features with bad acceptance crieteria and summary
bad_value=count_separate_issues()
bad_value["Over_due Features"]=no_of_over_due_features


# This creates a dashboard with any parameters we give == concentrating on quality
create_Bad_values_dashboard(bad_value)




# Filtering out all the Not-Good features
# filter_rows_with_missing()

# Filtering out features based on specific column name
# save_rows_with_empty_column("Due_date")











