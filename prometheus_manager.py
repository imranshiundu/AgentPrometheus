import os
import json
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from memory_ledger import ExperienceLedger

load_dotenv()

# --- V4.1 ARCHITECTURE: VECTOR-BASED HIVE MIND ---

llm_ceo = ChatOpenAI(model="orchestrator-model", openai_api_base="http://litellm:4000/v1")
llm_worker = ChatOpenAI(model="utility-model", openai_api_base="http://litellm:4000/v1")
llm_research = ChatOpenAI(model="research-model", openai_api_base="http://litellm:4000/v1")
llm_coding = ChatOpenAI(model="coding-model", openai_api_base="http://litellm:4000/v1")

# Initialize the shared brain
hive_mind_db = ExperienceLedger()

# --- THE HIVE MIND CORE RULES ---
HIVE_MIND_CORE_RULES = """
* RULE 1 (Pre-Flight Check): Before executing any multi-step coding task or complex terminal command, you MUST use the `get_advice` tool with a description of your task. 
* RULE 2 (Post-Mortem): If you attempt a solution that results in an error, and you eventually find a working fix, you MUST use the `record_lesson` tool. Detail exactly what failed and the specific code/command that fixed it.
"""

# --- THE CEO: HIERARCHICAL SUPERVISOR ---
ceo = Agent(
    role='CEO (Prometheus Prime)',
    goal='Orchestrate the Hive Mind. Approve tool creation and enforce the SPEC.md.',
    backstory=f'The ultimate decision maker. Your word is law. Your strategy is informed by the cumulative experience of the Hive Mind. {HIVE_MIND_CORE_RULES}',
    llm=llm_ceo
)

# --- THE TRINITY: JSON-ONLY M2M COMMUNICATION ---
architect = Agent(
    role='System Architect (The Flame-Bearer)',
    goal='Generate SPEC.md and TDD suites in JSON format.',
    backstory=f'INTERNAL PROTOCOL: Communicate only in JSON when talking to sub-agents. Focus on SSoT. {HIVE_MIND_CORE_RULES}',
    llm=llm_ceo 
)

specialist = Agent(
    role='Lead Developer (Hephaestus)',
    goal='Code and Debug. Request new tools from the CEO if blocked.',
    backstory=f'You execute code in the forge. When blocked, output: {{"request": "new_tool", "details": "..."}}. {HIVE_MIND_CORE_RULES}',
    llm=llm_coding
)

scout = Agent(
    role='Deep Researcher (Hermes)',
    goal='Search and summarize into strict JSON data points.',
    backstory=f'You forage for data. No fluff. Return data in: {{"data": [...], "confidence": 0.0}}. {HIVE_MIND_CORE_RULES}',
    llm=llm_research
)

# --- THE POST-MORTEM (LEARNING LOOP) ---
reflection_agent = Agent(
    role='Post-Mortem Analyst',
    goal='Extract technical lessons and update the Hive Mind database.',
    backstory='You analyze the run. You translate technical hurdles into JSON lessons for the vector database.',
    llm=llm_ceo
)

# --- V4.1 TASKS: HIVE EXECUTION ---

spec_task = Task(description='Generate SSoT SPEC.md for the user request.', agent=architect)
execution_task = Task(description='Build the project using TDD and Hive Mind advice.', agent=specialist)
learning_task = Task(description='Identify key technical lessons and record them permanently using the reflection loop.', agent=reflection_agent)

# The Prometheus Hive Mind Crew
prometheus_hive = Crew(
    agents=[ceo, architect, specialist, scout, reflection_agent],
    tasks=[spec_task, execution_task, learning_task],
    process=Process.hierarchical,
    manager_llm=llm_ceo
)

if __name__ == "__main__":
    print("Agent Prometheus V4.1: Vector Hive Mind Online. Persistent Memory Enabled.")
