import os
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

# Configure the unified LLM (pointing to LiteLLM Proxy)
llm = ChatOpenAI(
    model="gpt-4",
    openai_api_base=os.getenv("OPENAI_API_BASE", "http://litellm:4000/v1"),
    openai_api_key=os.getenv("OPENAI_API_KEY", "sk-prometheus-dummy-key")
)

# Define Prometheus Agents
architect = Agent(
    role='System Architect (Titan)',
    goal='Scaffold optimized project structures using gpt-engineer logic',
    backstory='Charged with bringing the fire of structure to the void of a new project.',
    verbose=True,
    allow_delegation=True,
    llm=llm
)

specialist = Agent(
    role='Lead Developer (Hephaestus)',
    goal='Implement and debug code using OpenHands execution loops',
    backstory='The master of the forge, capable of fixing any code in the sandbox.',
    verbose=True,
    allow_delegation=False,
    llm=llm
)

scout = Agent(
    role='Deep Researcher (Hermes)',
    goal='Gather cutting-edge tech data using AutoGPT autonomous search',
    backstory='The messenger who travels the far reaches of the web to find the truth.',
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# Define a sample Task for the fire-bringer
scaffold_task = Task(
    description='Initial scaffolding of a Python-based Hybrid Agent Framework named Prometheus.',
    agent=architect,
    expected_output='A directory structure and basic configuration files in the workspace.'
)

# Assemble the Crew
prometheus_crew = Crew(
    agents=[architect, specialist, scout],
    tasks=[scaffold_task],
    process=Process.sequential,
    verbose=True
)

if __name__ == "__main__":
    print("Agent Prometheus: Bringing the fire to your codebase...")
    # prometheus_crew.kickoff()  # Ready for execution
