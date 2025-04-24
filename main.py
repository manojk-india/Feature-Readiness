# imports ...
from utils import *
# import pandas as pd

# user query entry point 
query_user=input("Please enter your query: ")

def find_board_in_string(board_names, text):
    """
    Returns the first board name found in text, or None if none found.
    """
    for board in board_names:
        if board in text:
            return board
    return None

query=find_board_in_string(["APS", "DIS", "TES"],query_user)

# GuardRail
if query not in ["APS", "DIS", "TES"]:
    print("Board Not found.")



# # JIRA API query here ..rsult json file stored in data/result.json
get_board_features(query)

# # convert the aquired json to csv here and stored in data/API.csv
json_to_csv()

# # now checking acceptance_crieteria and summary and suggesting better changes and ading those to csv file itself 
process_evaluations()

# #Now we have to check all missing parameters
missing_value=count_empty_values("data/API.csv")

# # This creates a dashboard with any parameters we give == only concebtrating for missing values
create_missing_values_dashboard(missing_value)

# # Now worrying abt the quality of data == OverDue features , not so good Acceptance crieteria , Not so good summaries
# # overdue Task number returned and csv saved in overdue.csv
no_of_over_due_features=save_overdue_tasks()

# # No of features with bad acceptance crieteria and summary
bad_value=count_separate_issues()
bad_value["Over_due Features"]=no_of_over_due_features


# # This creates a dashboard with any parameters we give == concentrating on quality
create_Bad_values_dashboard(bad_value)


# Filtering out all the Not-Good features both missing and bad quality of acceptance crieteria == Not-Good-issues
filter_rows_with_missing_values_or_low_quality_data()

# # Filtering out features based on specific column name... can be invoked in runtime according to user input
save_rows_with_empty_column_and_low_quality_data("Over Due Features")











