# SYSTEM SPECIFICATION TEMPLATE (v1.1.0)

**Last Updated:** {{DATE}}
**Status:** [Draft / Active / In-Testing / Completed]
**Primary Agent Owner:** [e.g., OpenHands / gpt-engineer]

---

## 1. Core Objective
[Provide a strict 1-2 sentence description of the exact goal. No conversational fluff.]

## 2. Technical Stack & Constraints
[Agents love to invent dependencies. Lock them down here.]
* **Language:** [e.g., Python 3.11+]
* **Core Frameworks:** [List explicitly]
* **Environment:** [e.g., Docker, Local, etc.]
* **HARD CONSTRAINT:** Do not use any frameworks or libraries not explicitly listed above without Orchestrator approval.

## 3. In-Scope Features (Strict Execution)
[Be hyper-specific. If it is not on this list, it does not exist.]
1. **Feature A:** ...
2. **Feature B:** ...

## 4. OUT OF SCOPE (Anti-Hallucination Directives)
[This is the most important section. Explicitly list what the agents should NOT build to prevent feature creep.]
* **DO NOT** build a frontend web UI, dashboard, or HTML pages (unless specified).
* **DO NOT** implement user authentication (unless specified).
* **DO NOT** add support for platforms other than those listed.

## 5. Required File Structure
[Dictate exactly where files must go so agents don't lose them in the shared workspace.]
```text
/project_root
├── main.py
├── core/
├── tests/
└── requirements.txt
```

## 6. Acceptance Criteria (Definition of Done)
* `pytest tests/` runs and passes with 100% success.
* No console errors or stack traces in standard operation.
* Final output matches the exact format specified in Section 1.
