# here are our helper functions 
# imports here 
import json
import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
import csv
from typing import List, Dict
import pandas as pd
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np

from crew import *

import pandas as pd
from fpdf import FPDF
import ast


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
    with open(json_file, 'r',encoding='utf-8') as f:
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



def count_empty_values(csv_file: str) -> dict:
    """
    Count the number of empty (NaN or empty string) values in each column of the CSV file.

    Args:
        csv_file: Path to the CSV file

    Returns:
        Dictionary with column names as keys and count of empty values as values
    """
    df = pd.read_csv(csv_file)
    
    # Replace empty strings with NaN to count them as empty
    df.replace('', pd.NA, inplace=True)
    
    # Count NaN values per column
    empty_counts = df.isna().sum().to_dict()
    empty_counts["Overall_issues"]=len(df)
    
    return empty_counts

import pandas as pd


def filter_rows_with_missing_values_or_low_quality_data() -> None:
    """
    Reads a CSV file, filters rows with at least one missing value in any column,
    and saves those rows to a new CSV file.

    Args:
        csv_input: Path to the original CSV file
        csv_output: Path to save the filtered CSV file
    """
    csv_input="data/Final_API.csv"
    csv_output="data/Not-Good-issues.csv"
    df = pd.read_csv(csv_input)
    
    # Condition for missing values in any column
    missing_any = df.isna().any(axis=1)
    
    # Condition for Acceptance_result is 'Not Well Documented'
    acceptance_condition = df['Acceptance_result'].fillna('').str.strip() == 'Not Well Documented'
    
    # Condition for summary_result is 'Needs Improvement'
    summary_condition = df['summary_result'].fillna('').str.strip() == 'Needs Improvement'

    # need to add rows with overdue condition....
    # Convert Due_date to datetime
    df['Due_date'] = pd.to_datetime(df['Due_date'], errors='coerce')
    current_date = datetime.now()

    # Separate the conditions for clarity and correct operation
    overdue_condition = (
        (df['status'].fillna('').str.strip() != 'Done') & 
        (df['Due_date'] < current_date) & 
        (df['Due_date'].notna())
    )
    
    # Combine conditions: missing_any OR acceptance_condition OR summary_condition OR overdue_condition
    combined_condition = missing_any | acceptance_condition | summary_condition | overdue_condition
    
    # Filter rows
    filtered_df = df[combined_condition]

    
    # Save filtered rows to new CSV
    filtered_df.to_csv(csv_output, index=False)


# This function will be used when user asks abt some missing column
def save_rows_with_empty_column_and_low_quality_data(column_name: str) -> None:
    """
    Save rows to a new CSV where the specified column is empty or null.

    Args:
        csv_input: Path to the input CSV file.
        column_name: Column name to check for empty/null values.
        csv_output: Path to save the filtered CSV file.
    """
    csv_input="data/Final_API.csv"
    csv_output="data/user_specific_need.csv"

    df = pd.read_csv(csv_input)

    if(column_name=="Acceptance_result"):
        acceptance_issue = df['Acceptance_result'].isna() | (df['Acceptance_result'] == 'Not Well Documented')
        new_df=df[acceptance_issue]
        new_df.to_csv(csv_output, index=False)

    elif(column_name=="summary_result"):
        summary_issue = df['summary_result'] == 'Needs Improvement'
        new_df=df[summary_issue]
        new_df.to_csv(csv_output, index=False)

    elif(column_name=="Over Due Features"):
        df2 = pd.read_csv("data/overdue.csv")
        df2.to_csv(csv_output, index=False)
    else:
        # Treat empty strings as NaN for the specified column
        df[column_name].replace('', pd.NA, inplace=True)
        
        # Filter rows where the column is NaN (empty or null)
        filtered_df = df[df[column_name].isna()]
        
        # Save filtered rows to the output CSV
        filtered_df.to_csv(csv_output, index=False)



def save_overdue_tasks() -> int:
    """
    Extracts rows from CSV where due date is in the past and status is not 'Done'.
    
    Args:
        csv_input: Path to the input CSV file
        csv_output: Path to save the filtered CSV file
        
    Returns:
        Number of overdue tasks found
    """
    csv_input="data/Final_API.csv"
    csv_output="data/overdue.csv"
    # Read the CSV file
    df = pd.read_csv(csv_input)
    
    # Convert Due_date to datetime format (handling empty strings and invalid formats)
    df['Due_date'] = pd.to_datetime(df['Due_date'], errors='coerce')
    
    # Get current date
    current_date = datetime.now()
    
    # Filter rows where:
    # 1. Due_date is in the past (earlier than current date)
    # 2. Due_date is not empty/invalid
    # 3. Status is anything except "Done"
    filtered_df = df.loc[
        (df['Due_date'] < current_date) & 
        (df['Due_date'].notna()) & 
        (df['status'] != 'Done')
    ]
    
    # Save filtered rows to new CSV file
    filtered_df.to_csv(csv_output, index=False)
    
    return len(filtered_df)  # Return count of overdue items


def process_evaluations():
    """
    Process each row in the CSV file to evaluate acceptance criteria and summaries.
    
    Args:
        csv_file: Path to the input CSV file
        output_csv: Path to save the output CSV file
    """
    csv_file="data/API.csv"
    output_csv="data/Final_API.csv"
    # Load the CSV file with proper error handling
    try:
        df = pd.read_csv(csv_file)
        print(f"Successfully loaded CSV with {len(df)} rows")
    except FileNotFoundError:
        print(f"Error: File '{csv_file}' not found. Please check the file path.")
        return
    except Exception as e:
        print(f"Error loading CSV: {str(e)}")
        return
    
    # Create empty result columns
    df["Acceptance_result"] = ""
    df["Acceptance_improvement"] = None
    df["summary_result"] = ""
    df["summary_suggestion"] = ""

    
    # Process each row
    total_rows = len(df)
    for index, row in df.iterrows():
        try:
            # Progress indicator
            if index % 10 == 0:
                print(f"Processing row {index}/{total_rows}...")
            
            # Skip if required columns are missing
            if pd.isna(row.get('Acceptance_crieteria', None)) and pd.isna(row.get('summary', None)):
                continue
                
            # Evaluate acceptance criteria if present
            if not pd.isna(row.get('Acceptance_crieteria', None)):
                acceptance_result = evaluate_acceptance_criteria(row['Acceptance_crieteria'])
                df.at[index, "Acceptance_result"] = acceptance_result.get("classification", "")
                df.at[index, "Acceptance_improvement"] = {
                    'strengths': acceptance_result.get('strengths', []),
                    'improvement_areas': acceptance_result.get('improvement_areas', []),
                    'revised_version': acceptance_result.get('revised_version', '')
                }
            
            # Evaluate summary and description if both present
            if not pd.isna(row.get('summary', None)) and not pd.isna(row.get('description', None)):
                summary_result = evaluate_summary(row['summary'], row['description'])
                df.at[index, "summary_result"] = summary_result.get("classification", "")
                df.at[index, "summary_suggestion"] = summary_result.get("improved_version", "")
                
        except Exception as e:
            print(f"Error processing row {index}: {str(e)}")
    
    # Save to new CSV
    try:
        df.to_csv(output_csv, index=False)
        print(f"Successfully saved results to {output_csv}")
        return output_csv
    except Exception as e:
        print(f"Error saving CSV: {str(e)}")
        return None

def count_separate_issues() -> dict:
    """
    Counts rows with issues in Acceptance_result and summary_result separately.
    
    Args:
        csv_file: Path to the CSV file
        
    Returns:
        Dictionary with separate counts for acceptance and summary issues.
    """
    csv_file="data/Final_API.csv"
    df = pd.read_csv(csv_file)
    
    # Treat empty strings as NaN for accurate missing detection
    df['Acceptance_result'].replace('', np.nan, inplace=True)
    df['summary_result'].replace('', np.nan, inplace=True)
    
    # Count: Acceptance_result is NaN or 'Not Well Documented'
    acceptance_issue = df['Acceptance_result'].isna() | (df['Acceptance_result'] == 'Not Well Documented')
    acceptance_issue_count = acceptance_issue.sum()
    
    # Count: summary_result is 'Needs Improvement'
    summary_issue = df['summary_result'] == 'Needs Improvement'
    summary_issue_count = summary_issue.sum()
    
    return {
        'acceptance_issue_count': int(acceptance_issue_count),
        'summary_issue_count': int(summary_issue_count),
        'Overall_issues':len(df)
    }




def create_missing_values_dashboard(missing_counts: dict, output_file: str = 'Report/missing_values_dashboard.png'):
    """
    Creates a professional dashboard visualizing missing values percentages
    
    Args:
        missing_counts: Dictionary with columns and their missing value counts
        output_file: Path to save the output image
        
    Returns:
        Path to the saved dashboard image
    """
    # Extract keys and values
    keys = list(missing_counts.keys())
    values = list(missing_counts.values())
    
    # Calculate total rows from Overall_issues
    total_rows = missing_counts.get('Overall_issues', 10)
    
    # Remove Overall_issues from keys and values for plotting
    if 'Overall_issues' in keys:
        idx = keys.index('Overall_issues')
        keys.pop(idx)
        values.pop(idx)
    
    # Calculate percentages
    percentages = [(v / total_rows) * 100 for v in values]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_facecolor('#f0f0f0')
    
    # Bar chart
    bars = ax.barh(keys, percentages, color='#4c72b0')
    
    # Add text labels
    for bar, pct, count in zip(bars, percentages, values):
        width = bar.get_width()
        ax.text(width + 1, bar.get_y() + bar.get_height()/2, 
                f'{pct:.1f}% ({count})',
                va='center', fontsize=12, color='#333333')
    
    # Title and labels
    ax.set_title('Missing Values Percentage per Column', fontsize=18, 
                 fontweight='bold', color='#222222')
    ax.set_xlabel('Percentage (%)', fontsize=14)
    ax.set_xlim(0, max(percentages) + 10)
    
    # Remove spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    # Grid
    ax.xaxis.grid(True, linestyle='--', alpha=0.7)
    ax.yaxis.grid(False)
    
    # Invert y-axis for better readability
    ax.invert_yaxis()
    
    # Save figure
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close(fig)
    
    return output_file





def create_Bad_values_dashboard(missing_counts: dict, output_file: str = 'Report/Bad_values_dashboard.png'):
    """
    Creates a professional dashboard visualizing missing values percentages
    
    Args:
        missing_counts: Dictionary with columns and their missing value counts
        output_file: Path to save the output image
        
    Returns:
        Path to the saved dashboard image
    """
    # Extract keys and values
    keys = list(missing_counts.keys())
    values = list(missing_counts.values())
    
    # Calculate total rows from Overall_issues
    total_rows = missing_counts.get('Overall_issues', 10)
    
    # Remove Overall_issues from keys and values for plotting
    if 'Overall_issues' in keys:
        idx = keys.index('Overall_issues')
        keys.pop(idx)
        values.pop(idx)
    
    # Calculate percentages
    percentages = [(v / total_rows) * 100 for v in values]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_facecolor('#f0f0f0')
    
    # Bar chart
    bars = ax.barh(keys, percentages, color='#4c72b0')
    
    # Add text labels
    for bar, pct, count in zip(bars, percentages, values):
        width = bar.get_width()
        ax.text(width + 1, bar.get_y() + bar.get_height()/2, 
                f'{pct:.1f}% ({count})',
                va='center', fontsize=12, color='#333333')
    
    # Title and labels
    ax.set_title('Bad Values Percentage per Column', fontsize=18, 
                 fontweight='bold', color='#222222')
    ax.set_xlabel('Percentage (%)', fontsize=14)
    ax.set_xlim(0, max(percentages) + 10)
    
    # Remove spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    # Grid
    ax.xaxis.grid(True, linestyle='--', alpha=0.7)
    ax.yaxis.grid(False)
    
    # Invert y-axis for better readability
    ax.invert_yaxis()
    
    # Save figure
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close(fig)
    
    return output_file



def clean_latin1(text):
    if not isinstance(text, str):
        return ''
    replacements = {
        '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"',
        '\u2013': '-', '\u2014': '-', '\u2026': '...',
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode('latin-1', 'replace').decode('latin-1')

class PDFReport(FPDF):
    def header(self):
        self.image("wells-image.png", x=10, y=8, w=60)  # Adjust path/size as needed
        self.ln(20)
        self.set_font('helvetica', 'B', 14)
        self.cell(0, 10, 'JIRA Summary Evaluation Report', 0, 1, 'C')
        self.ln(5)
    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_summary_report(csv_file="data/Final_API.csv", pdf_file="Report/summary_report.pdf"):
    df = pd.read_csv(csv_file)

    pdf = PDFReport()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font('helvetica', '', 11)

    for idx, row in df.iterrows():
        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(0, 10, clean_latin1(f"Feature Key: {row.get('key', '')}"), ln=True)
        pdf.set_font('helvetica', '', 11)
        pdf.multi_cell(0, 8, clean_latin1(f"Summary: {row.get('summary', '')}"))
        pdf.ln(1)
        pdf.set_font('helvetica', 'B', 11)
        pdf.cell(0, 10, clean_latin1('Summary Evaluation Result:'), ln=True)
        pdf.set_font('helvetica', '', 11)
        pdf.multi_cell(0, 8, clean_latin1(str(row.get('summary_result', ''))))
        pdf.ln(2)
        pdf.set_font('helvetica', 'B', 11)
        pdf.cell(0, 10, clean_latin1('Suggested Improved Summary:'), ln=True)
        pdf.set_font('helvetica', '', 11)
        suggestion = row.get('summary_suggestion', '')
        if suggestion and str(suggestion).strip():
            pdf.multi_cell(0, 8, clean_latin1(str(suggestion)))
        else:
            pdf.cell(0, 8, 'None', ln=True)
        pdf.ln(10)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(10)

    pdf.output(pdf_file)

class PDFReport1(FPDF):
    def header(self):
        self.image("wells-image.png", x=10, y=8, w=60)  # Adjust path/size as needed
        self.ln(20)
        self.set_font('helvetica', 'B', 14)
        self.cell(0, 10, 'Acceptance_crieteria evaluation Report', 0, 1, 'C')
        self.ln(5)
    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_acceptance_improvement_report(csv_file="data/user_specific_need.csv", pdf_file="Report/acceptance_report.pdf"):
    df = pd.read_csv(csv_file)

    pdf = PDFReport1()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font('helvetica', '', 11)  # Use built-in font

    for idx, row in df.iterrows():
        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(0, 10, clean_latin1(f"Feature Key: {row.get('key', '')}"), ln=True)
        pdf.set_font('helvetica', '', 11)

        pdf.multi_cell(0, 8, clean_latin1(f"Summary: {row.get('summary', '')}"))
        pdf.ln(1)
        pdf.multi_cell(0, 8, clean_latin1(f"Description: {row.get('description', '')}"))
        pdf.ln(1)
        pdf.multi_cell(0, 8, clean_latin1(f"Acceptance Criteria: {row.get('Acceptance_crieteria', '')}"))
        pdf.ln(5)

        improvement_str = row.get('Acceptance_improvement', '{}')
        try:
            improvement_dict = ast.literal_eval(improvement_str) if isinstance(improvement_str, str) else {}
        except Exception:
            improvement_dict = {}

        strengths = improvement_dict.get('strengths', [])
        improvement_areas = improvement_dict.get('improvement_areas', [])
        revised_version = improvement_dict.get('revised_version', '')

        pdf.set_font('helvetica', 'B', 11)
        pdf.cell(0, 10, clean_latin1('Strengths:'), ln=True)
        pdf.set_font('helvetica', '', 11)
        if strengths:
            for s in strengths:
                pdf.multi_cell(0, 8, clean_latin1(f"- {s}"))
        else:
            pdf.cell(0, 8, 'None', ln=True)

        pdf.ln(2)
        pdf.set_font('helvetica', 'B', 11)
        pdf.cell(0, 10, clean_latin1('Improvement Areas:'), ln=True)
        pdf.set_font('helvetica', '', 11)
        if improvement_areas:
            for imp in improvement_areas:
                pdf.multi_cell(0, 8, clean_latin1(f"- {imp}"))
        else:
            pdf.cell(0, 8, 'None', ln=True)

        pdf.ln(2)
        pdf.set_font('helvetica', 'B', 11)
        pdf.cell(0, 10, clean_latin1('Revised Version:'), ln=True)
        pdf.set_font('helvetica', '', 11)
        if revised_version:
            pdf.multi_cell(0, 8, clean_latin1(revised_version))
        else:
            pdf.cell(0, 8, 'None', ln=True)

        pdf.ln(10)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(10)

    pdf.output(pdf_file)