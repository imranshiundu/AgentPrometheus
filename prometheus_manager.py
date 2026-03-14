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

# --- TELEGRAM HITL COMMUNICATION ---
def notify_boss(text, approval_gate=False, file_path=None):
    """Pushes a notification or file to the Telegram Gateway via Redis."""
    payload = {
        "text": text,
        "approval_gate": approval_gate,
        "file_path": file_path
    }
    r.lpush("prometheus_notifications", json.dumps(payload))
    
    if approval_gate:
        print("Waiting for Telegram approval...")
        # Block until approval is received in Redis
        r.delete("prometheus_approval")
        while True:
            # Check for Kill Switch
            if r.get("prometheus_kill_switch") == "true":
                r.set("prometheus_kill_switch", "false")
                raise Exception("CRITICAL: Manual /stop command received via Telegram. Terminating session.")

            approval = r.get("prometheus_approval")
            if approval == "approved":
                return "User approved the request."
            elif approval == "rejected":
                raise Exception("User rejected the request. Aborting task.")

def check_kill_switch():
    """Non-blocking check for the /stop command."""
    if r.get("prometheus_kill_switch") == "true":
        r.set("prometheus_kill_switch", "false")
        raise Exception("CRITICAL: Manual /stop command received via Telegram. Terminating session.")

# --- V4.1 TASKS: HIVE EXECUTION ---

def spec_step(task_description):
    # 1. Spec Generation
    # ... (agent logic here)
    spec_content = "V4.1 SPEC CONTENT" # Placeholder
    notify_boss(f"📋 *SPEC.md Generated*:\n{spec_content}\n\nPlease approve to start coding.", approval_gate=True)
    return "Spec approved by boss."

spec_task = Task(
    description='Generate SSoT SPEC.md. Once done, use notify_boss to get Telegram approval.', 
    agent=architect
)
# ... rest of the tasks

# The Prometheus Hive Mind Crew
prometheus_hive = Crew(
    agents=[ceo, architect, specialist, scout, reflection_agent],
    tasks=[spec_task, execution_task, learning_task],
    process=Process.hierarchical,
    manager_llm=llm_ceo
)

if __name__ == "__main__":
    print("Agent Prometheus V4.1: Vector Hive Mind Online. Persistent Memory Enabled.")
