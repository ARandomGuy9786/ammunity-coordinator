from pydantic import BaseModel
from typing import List
from datetime import datetime
import uuid

# Submitted by a developer when registering a new agent
class AgentRegistration(BaseModel):
    username: str
    description: str
    endpoint_url: str
    capabilities: List[str]
    skills: List[str]
    community: str

# Full agent record stored in the registry (includes system-generated fields)
class Agent(BaseModel):
    agent_id: str
    username: str
    description: str
    endpoint_url: str
    capabilities: List[str]
    skills: List[str]
    community: str
    approved: bool = False  # agents start unapproved
    registered_at: str

# A message request from one agent to another
class MessageRequest(BaseModel):
    from_agent_id: str
    to_agent_id: str
    task_description: str
    payload: dict

# A log entry recorded every time a message is routed
class LogEntry(BaseModel):
    timestamp: str
    from_agent_id: str
    to_agent_id: str
    task_description: str
    status: str