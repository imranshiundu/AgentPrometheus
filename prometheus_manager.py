import os
import json
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

# --- V3 ARCHITECTURE: MICROSERVICES & SPEC GUARDIANS ---

llm_manager = ChatOpenAI(model="orchestrator-model", openai_api_base="http://litellm:4000/v1")
llm_economy = ChatOpenAI(model="utility-model", openai_api_base="http://litellm:4000/v1")
llm_research = ChatOpenAI(model="research-model", openai_api_base="http://litellm:4000/v1")
llm_coding = ChatOpenAI(model="coding-model", openai_api_base="http://litellm:4000/v1")

# The Architect: Creates the Single Source of Truth (SSoT)
architect = Agent(
    role='System Architect (The Flame-Bearer)',
    goal='Generate strict SPEC.md and TDD test suites',
    backstory='You translate human desire into machine-readable specs and tests. You never leave grey areas.',
    llm=llm_manager
)

# The Specialist: Isolated Microservice (OpenHands / AutoGPT Wrappers)
specialist = Agent(
    role='Lead Developer (Hephaestus Service)',
    goal='Execute coding tasks strictly according to the SPEC.md',
    backstory='A master of code who only works when given a clear SPEC.md and a set of failing tests.',
    llm=llm_coding
)

# The Spec Guardian: Enforcement & QA
guardian = Agent(
    role='Spec Guardian (The Judge)',
    goal='Reject any code that drifts from the SPEC.md or includes Out-of-Scope features',
    backstory='A cold, logical auditor. You do not care about effort; you only care about adherence to the specification.',
    llm=llm_manager
)

# --- V3 PIPELINE: TDD & SPEC LOCKDOWN ---

spec_task = Task(
    description='Analyze the user request and generate a strict SPEC.md using the template. Include an "Out-of-Scope" section.',
    agent=architect,
    expected_output='A professional SPEC.md in the workspace.'
)

test_task = Task(
    description='Based on the SPEC.md, generate a suite of failing PyTest tests in /workspace/tests.',
    agent=architect,
    expected_output='A suite of Python test files.'
)

coding_task = Task(
    description='Implement the logic in /workspace strictly following the SPEC.md until all tests pass.',
    agent=specialist,
    expected_output='Clean, passing code.'
)

qa_task = Task(
    description='Audit the code. Check specifically for Out-of-Scope "feature creep". If detected, send back for removal.',
    agent=guardian,
    expected_output='A "Pass/Fail" report based on SPEC.md adherence.'
)

prometheus_crew = Crew(
    agents=[architect, specialist, guardian],
    tasks=[spec_task, test_task, coding_task, qa_task],
    process=Process.hierarchical,
    manager_llm=llm_manager
)

if __name__ == "__main__":
    print("Agent Prometheus V3: Microservices & SSoT Enforcement...")
