# importing required modules 
from crewai import Crew,Agent,Task,LLM
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Literal

# Initialize LLM model
llm = LLM(
    model="sambanova/DeepSeek-R1-Distill-Llama-70B",
    temperature=0.1,
    max_tokens=2048
)


load_dotenv()  # Load environment variables

# pydantic classes
class Evaluated_metrics(BaseModel):
    classification: str
    strengths: list[str]
    improvement_areas: list[str]
    revised_version: str

class Evaluated_summary(BaseModel):
    classification: str
    improved_version: str


# Define the evaluation agent
criteria_evaluator = Agent(
    role="Acceptance Criteria Quality Evaluator",
    goal="Evaluate if acceptance criteria is well-documented and understandable by non-technical users",
    backstory="""You are an expert in User Story quality assessment with deep knowledge of 
    acceptance criteria best practices. You specialize in evaluating the clarity, 
    completeness and accessibility of Given/When/Then formatted requirements.""",
    llm=llm,
    verbose=True,
)

# Define the evaluation task with a detailed prompt
evaluation_task = Task(
    description="""
    Note: Just classify ..no function calling is required 
    Evaluate the quality of the following acceptance criteria 
    

    {acceptance_criteria}
    
    By understanding acceptance crieteria and analyzing it do the following 
    #) classification : Well Documented or Not Well Documented
    #) strengths : ["strength1", "strength2"...],
    #) improvement_areas: ["area1", "area2"...],
    #) revised_version: "Proper acceptance crieteria without missing anything in Given When Then format"

    While classifying it as well documented or not consider th below 
    First of all check whether it is in Given When Then format or not...if not directly classify it as Not Well Documented
    Then even if it is Given When Then format .....check whether its written in a wells understandable way and then classify accordingly 
    
    Provide specific feedback on strengths and areas for improvement.

    Even if you feel the acceptance crieteria is okay just classify it as well documneted . only classify it as poor only if you feel it is very poor

    Note : Dont miss out any parameters mentionedd at all.....
    """,
    agent=criteria_evaluator,
    expected_output="""
        "classification": Well Documented or Not Well Documented
        "strengths": ["strength1", "strength2"...],
        "improvement_areas": ["area1", "area2"...],
        "revised_version": "Proper acceptance crieteria without missing anything in Given When Then format"
    """,
    output_pydantic=Evaluated_metrics
)



# Create the crew
criteria_crew = Crew(
    agents=[criteria_evaluator],
    tasks=[evaluation_task],
    verbose=True
)

# Example usage
def evaluate_acceptance_criteria(criteria_text):
    result = criteria_crew.kickoff(inputs={"acceptance_criteria": criteria_text})
    return {
            "classification":result["classification"],
            "strengths":result["strengths"],
            "improvement_areas":result["improvement_areas"],
            "revised_version":result["revised_version"],
            }


####################################################################################### Now for valid summary with given description

evaluator = Agent(
        role="JIRA Quality Analyst",
        goal="Evaluate summary using description and suggest better summaries",
        backstory="Expert in technical documentation who ensures clarity for all audiences",
        llm=llm
    )
    
# Create evaluation task
evaluation_task = Task(
   Description="""
   Evaluate this JIRA description and determine if the summary is well-written:
    
    CURRENT SUMMARY: {summary}
    
    DESCRIPTION: {description}
    
    Focus ONLY on:
    1. IS the summary well-written
    2. Is it representing what the feature is supposed to do
    3. Is it clear and concise
    
    Provide ONLY:
    - "GOOD" or "NEEDS IMPROVEMENT" verdict on the summary based on description
    - If needed, a suggested improved summary that better reflects the description
    Summary is like heading ..it should be clear and concise and should represent what the feature is supposed to do.
    Even if it is decent classify it as GOOD but also give your suggested summary that captures the key benefits and functionality of the feature
    """,
    agent=evaluator,
    output_pydantic=Evaluated_summary,
    expected_output="""
    classification: 'Good' or 'Needs Improvement'
    improved_version: improved summary based on criteria
    """
)

# Create and execute crew
crew = Crew(
    agents=[evaluator],
    tasks=[evaluation_task],
)

def evaluate_summary(summary,description):
    # Get results
    result = crew.kickoff(inputs={"summary": summary, "description": description})
    return {
        "classification":result["classification"],
        "improved_version":result["improved_version"]
    }