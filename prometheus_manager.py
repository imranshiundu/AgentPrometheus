import os
import json
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

# --- V4 ARCHITECTURE: THE HIVE MIND & CEO ---

llm_ceo = ChatOpenAI(model="orchestrator-model", openai_api_base="http://litellm:4000/v1")
llm_worker = ChatOpenAI(model="utility-model", openai_api_base="http://litellm:4000/v1")
llm_research = ChatOpenAI(model="research-model", openai_api_base="http://litellm:4000/v1")
llm_coding = ChatOpenAI(model="coding-model", openai_api_base="http://litellm:4000/v1")

# --- HIVE MIND MEMORY (EXPERIENCE LEDGER) ---
def get_lessons_learned():
    try:
        with open("workspace/experience.json", "r") as f:
            return f.read()
    except:
        return "{}"

# --- THE CEO: HIERARCHICAL SUPERVISOR ---
ceo = Agent(
    role='CEO (Prometheus Prime)',
    goal='Orchestrate the Hive Mind. Approve tool creation and enforce the SPEC.md.',
    backstory=f'The ultimate decision maker. Your word is law. Current context from previous runs: {get_lessons_learned()}',
    llm=llm_ceo
)

# --- THE TRINITY: JSON-ONLY M2M COMMUNICATION ---
architect = Agent(
    role='System Architect (The Flame-Bearer)',
    goal='Generate SPEC.md and TDD suites in JSON format.',
    backstory='INTERNAL PROTOCOL: Communicate only in JSON when talking to sub-agents. Focus on SSoT.',
    llm=llm_ceo 
)

specialist = Agent(
    role='Lead Developer (Hephaestus)',
    goal='Code and Debug. Request new tools from the CEO if blocked.',
    backstory='You execute code in the forge. When blocked, output: {"request": "new_tool", "details": "..."}.',
    llm=llm_coding
)

scout = Agent(
    role='Deep Researcher (Hermes)',
    goal='Search and summarize into strict JSON data points.',
    backstory='You forage for data. No fluff. Return data in: {"data": [...], "confidence": 0.0}.',
    llm=llm_research
)

# --- THE POST-MORTEM (LEARNING LOOP) ---
reflection_agent = Agent(
    role='Post-Mortem Analyst',
    goal='Extract technical lessons and update the experience.json ledger.',
    backstory='You analyze the run. If Hephaestus failed, you record why (e.g., Python version mismatch).',
    llm=llm_ceo
)

# --- V4 TASKS: HIVE EXECUTION ---

# 1. Spec Lockdown
spec_task = Task(description='Generate SSoT SPEC.md for the user request.', agent=architect)

# 2. Execution with TDD
execution_task = Task(description='Build the project. If you need a script to scrape data, request a tool.', agent=specialist)

# 3. Learning (The Reflection)
learning_task = Task(
    description='Record any technical hurdles encountered and how they were solved to workspace/experience.json.', 
    agent=reflection_agent
)

# The Prometheus Hive Mind Crew
prometheus_hive = Crew(
    agents=[ceo, architect, specialist, scout, reflection_agent],
    tasks=[spec_task, execution_task, learning_task],
    process=Process.hierarchical,
    manager_llm=llm_ceo
)

if __name__ == "__main__":
    print("Agent Prometheus V4: Hive Mind Online. Initializing Experience Ledger...")
