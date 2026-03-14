# Agent Prometheus: Agent Abilities & Roles

This document details the specific "superpowers" that each integrated framework contributes to the Agent Prometheus hybrid system.

## 1. The Architect (powered by gpt-engineer)
**Primary Focus:** Project Scaffolding & Requirement Analysis.
- **Whole-Codebase Vision:** Can generate the entire initial file structure from a single prompt.
- **Clarification Ritual:** Proactively asks the user high-value questions to resolve ambiguities before coding starts.
- **Tech Stack Selection:** Automatically determines the best libraries and folder patterns for the user's specific goal.

## 2. The Specialist (powered by OpenHands)
**Primary Focus:** Hands-on Coding & Sandboxed Execution.
- **Terminal Interaction:** Can run bash commands, install dependencies, and execute scripts in a safe Docker environment.
- **Self-Correction Loop:** If the code fails a test, it reads the error log, modifies the code, and tries again autonomously.
- **Browser-Based Debugging:** Can interact with web pages to test frontend code rendering.

## 3. The Scout (powered by AutoGPT)
**Primary Focus:** Autonomous Research & Knowledge Retrieval.
- **Unstructured Goal Seeking:** Give it a vague research goal (e.g., "Find the most secure way to handle JWT in 2024"), and it will navigate the web until it finds the answer.
- **Tool Creation:** Can write its own small helper scripts during a research task to process data it finds online.
- **Long-term Memory:** Retains information from past search steps to inform complex multi-page research.

## 4. The Orchestrator (powered by crewAI)
**Primary Focus:** Strategy, Delegation, and Quality Assurance.
- **Role-Playing System:** Manages the communication between the Architect, Specialist, and Scout agents.
- **Hierarchical Thinking:** Can act as a "Manager" that reviews the work of other agents and sends it back for revision if quality standards aren't met.
- **Process Orchestration:** Switches between frameworks based on the project phase (e.g., calling the Architect for Phase 1 and the Specialist for Phase 3).

---

## Ability Matrix

| Ability | gpt-engineer | OpenHands | AutoGPT | crewAI |
| :--- | :---: | :---: | :---: | :---: |
| **Code Scaffolding** | ⭐⭐⭐ | ⚪ | ⚪ | ⚪ |
| **Sandbox Execution** | ⚪ | ⭐⭐⭐ | ⚪ | ⚪ |
| **Deep Research** | ⚪ | ⚪ | ⭐⭐⭐ | ⚪ |
| **Multi-Agent Management** | ⚪ | ⚪ | ⚪ | ⭐⭐⭐ |
| **Self-Correction** | ⚪ | ⭐⭐⭐ | ⭐⭐ | ⚪ |
| **Requirement Analysis** | ⭐⭐⭐ | ⚪ | ⚪ | ⭐⭐ |
