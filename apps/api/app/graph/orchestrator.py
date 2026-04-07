from typing import Annotated, Optional, TypedDict
from operator import add

from langgraph.graph import END, StateGraph
from app.core.llm import call_llm


class AgentState(TypedDict):
    messages: Annotated[list, add]
    user_id: int
    task_id: Optional[int]
    context: dict
    route: str
    final_response: str


def intake_node(state: AgentState):
    return state


def enrich_context_node(state: AgentState):
    return state


def classify_node(state: AgentState):
    user_text = state["messages"][-1]["content"].lower()

    action_keywords = [
        "create file", "write file", "make file",
        "fetch url", "call api", "http get",
        "github repo", "repo info",
    ]
    task_keywords = [
        "build", "create app", "generate plan",
        "set up", "implement", "design system",
    ]

    if any(k in user_text for k in action_keywords):
        state["route"] = "action"
    elif any(k in user_text for k in task_keywords):
        state["route"] = "task"
    else:
        state["route"] = "chat"

    return state


def plan_node(state: AgentState):
    if state["route"] == "task":
        state["final_response"] = (
            "Task recognized. This request has been tracked for execution."
        )
        return state

    if state["route"] == "action":
        state["final_response"] = (
            "Action recognized. Use the /actions endpoint. "
            "Guardrails enforce policy: actions may be allowed, blocked, or require approval."
        )
        return state

    memory_lines = state.get("context", {}).get("memory_snippets", [])
    memory_context = "\n".join(memory_lines) if memory_lines else "No memory context available."

    system_prompt = (
        "You are Jarvis Assistant. "
        "Be concise, useful, structured, and execution-oriented. "
        "If asked to perform an action beyond current capabilities, say so clearly."
    )

    user_prompt = f"Memory context:\n{memory_context}\n\nUser request:\n{state['messages'][-1]['content']}"
    response = call_llm(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )

    state["final_response"] = response
    return state


def execute_node(state: AgentState):
    return state


def complete_node(state: AgentState):
    return state


def build_orchestrator():
    graph = StateGraph(AgentState)

    graph.add_node("intake", intake_node)
    graph.add_node("enrich_context", enrich_context_node)
    graph.add_node("classify", classify_node)
    graph.add_node("plan", plan_node)
    graph.add_node("execute", execute_node)
    graph.add_node("complete", complete_node)

    graph.set_entry_point("intake")
    graph.add_edge("intake", "enrich_context")
    graph.add_edge("enrich_context", "classify")
    graph.add_edge("classify", "plan")
    graph.add_edge("plan", "execute")
    graph.add_edge("execute", "complete")
    graph.add_edge("complete", END)

    return graph.compile()
