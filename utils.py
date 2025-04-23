# here are our helper functions 
# imports here 
import json
import os
import requests
from requests.auth import HTTPBasicAuth
from typing import Dict
from dotenv import load_dotenv


load_dotenv()


def get_board_features(
    board_name: str,
    max_results: int = 100
) -> Dict:
    id_dict = {
        "APS": 34,
        "DIS": 2,
        "TES": 35
    }

    board_id = id_dict[board_name]
    email = "manokalyan2004@gmail.com"
    api_token = os.getenv('JIRA_API_TOKEN')

    base_url = f"https://wellsfargo-jira-test.atlassian.net/rest/agile/1.0/board/{board_id}/issue"
    headers = {"Accept": "application/json"}
    auth = HTTPBasicAuth(email, api_token)
    
    all_issues = []
    start_at = 0
    total = None

    while True:
        params = {
            "startAt": start_at,
            "maxResults": max_results,
            "jql": "issuetype = Feature"
        }

        response = requests.get(
            url=base_url,
            headers=headers,
            auth=auth,
            params=params
        )

        if response.status_code != 200:
            raise Exception(f"API request failed: {response.status_code} - {response.text}")

        data = response.json()
        all_issues.extend(data.get("issues", []))
        
        # Get total number of issues from first response
        if total is None:
            total = data.get('total', 0)
        
        # Calculate if we've fetched all issues
        if len(data.get('issues', [])) < max_results or start_at + max_results >= total:
            break
            
        start_at += max_results

    with open('data/result.json', 'w') as f:
        json.dump({"features": all_issues}, f, indent=2)

    return {"features": all_issues}




# This function is for converting json to csv file 
import json
import csv
from typing import List, Dict

def json_to_csv() -> None:
    """
    Convert Jira features JSON to CSV with specified fields
    
    Args:
        json_file: Path to input JSON file
        csv_file: Path to output CSV file
    """
    json_file="data/result.json"

    # Define CSV field headers
    field_names = [
        "key",
        "parent_id",
        "summary",
        "description",
        "Acceptance_crieteria",
        "labels",
        "components",
        "parent_key",
        "Requested_by",
        "timeestimate",
        "Due_date",
        "status"
    ]

    # Read JSON data
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Prepare CSV rows
    rows = []
    for feature in data.get('features', []):
        fields = feature.get('fields', {})
        
        # Handle nested fields and potential missing data
        row = {
            "key": feature.get('key', ''),
            "parent_id": fields.get('parent', {}).get('id', ''),
            "summary": fields.get('summary', ''),
            "description": fields.get('description', ''),
            "Acceptance_crieteria": fields.get('customfield_10042', ''),
            "labels": ', '.join(fields.get('labels', [])),
            "components": ', '.join([c.get('name', '') for c in fields.get('components', [])]),
            "parent_key": fields.get('parent', {}).get('key', ''),
            "Requested_by": fields.get('customfield_10043', ''),
            "timeestimate": fields.get('timeestimate', ''),
            "Due_date": fields.get('customfield_10040', ''),
            "status": fields.get('statusCategory', {}).get('name', '')
        }
        rows.append(row)

    # Write to CSV
    with open("data/API.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(rows)


