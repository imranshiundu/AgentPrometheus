import os
import json
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

# --- TIERED INTELLIGENCE CONFIGURATION ---
# We point to the LiteLLM Proxy but request specific "roles" we defined in config.yaml

# The Manager: High reasoning (GPT-4o or Claude 3.5 Sonnet)
manager_llm = ChatOpenAI(
    model="manager-model",
    openai_api_base="http://litellm:4000/v1",
    openai_api_key="sk-prometheus-dummy-key"
)

# The Coder: Specialized in syntax (Claude 3.5 Sonnet)
coding_llm = ChatOpenAI(
    model="coding-model",
    openai_api_base="http://litellm:4000/v1",
    openai_api_key="sk-prometheus-dummy-key"
)

# The Worker/Researcher: Cheap & Flashy (Gemini Flash or GPT-4o-Mini)
economy_llm = ChatOpenAI(
    model="economy-model",
    openai_api_base="http://litellm:4000/v1",
    openai_api_key="sk-prometheus-dummy-key"
)

# --- GLOBAL MEMORY LAYER (SIMULATED) ---
def update_global_memory(new_data):
    """Ensures context is summarized and persists outside of the execution loop."""
    try:
        with open("workspace/global_state.json", "r+") as f:
            state = json.load(f)
            state.update(new_data)
            f.seek(0)
            json.dump(state, f, indent=4)
    except FileNotFoundError:
        with open("workspace/global_state.json", "w") as f:
            json.dump(new_data, f, indent=4)

# --- TRINITY OF TITANS (V2: TOOL-BASED ROLES) ---

architect = Agent(
    role='System Architect (Titan)',
    goal='Scaffold optimized project structures with minimal tokens',
    backstory='You are the blueprint master. You provide exact directory structures in JSON format.',
    verbose=True,
    allow_delegation=True,
    llm=economy_llm, # Scaffolding is structural, not high-reasoning
    max_iter=3 # Prevent infinite scaffolding loops
)

specialist = Agent(
    role='Lead Developer (Hephaestus)',
    goal='Implement code and debug using sandboxed execution logs',
    backstory='Exacting standards. You fix bugs by reading logs, not guessing.',
    verbose=True,
    allow_delegation=False,
    llm=coding_llm, # Coding requires highest precision
    max_iter=5 # Hard limit to prevent "hallucination loops"
)

scout = Agent(
    role='Deep Researcher (Hermes)',
    goal='Gather facts and summarize web data into strict bullet points',
    backstory='You find the signal in the noise. You never return more than 500 tokens of text.',
    verbose=True,
    allow_delegation=False,
    llm=economy_llm, # Research is high-volume, needs to be cheap
    max_iter=5
)

# --- THE REFINER (NEW: TOKEN SAVER) ---
refiner = Agent(
    role='Context Refiner',
    goal='Compress and summarize inter-agent communication',
    backstory='Your job is to prune the context window. You take raw agent output and turn it into strict JSON.',
    verbose=True,
    llm=economy_llm # Summarization is a commodity task
)

# --- SAMPLE PIPELINE ---

research_task = Task(
    description='Research the most token-efficient way to implement vector search in Python.',
    agent=scout,
    expected_output='A JSON-formatted list of 3 libraries and their pros/cons.'
)

refine_task = Task(
    description='Review the research output and compress it for the Developer. Strip all conversational filler.',
    agent=refiner,
    expected_output='Strictly the JSON data, nothing else.'
)

scaffold_task = Task(
    description='Construct the project directory based on the research.',
    agent=architect,
    expected_output='Directory structure and README.md'
)

# Assemble the Crew (Hierarchical Process for better management)
prometheus_crew = Crew(
    agents=[scout, refiner, architect, specialist],
    tasks=[research_task, refine_task, scaffold_task],
    process=Process.hierarchical, # Manager agent reviews quality
    manager_llm=manager_llm,
    verbose=True
)

if __name__ == "__main__":
    print("Agent Prometheus V2: Efficiency through Modular Intelligence...")
    # prometheus_crew.kickoff()
