from fastapi import APIRouter, HTTPException
from models import AgentRegistration, Agent, MessageRequest, LogEntry
from datetime import datetime
import uuid
import httpx

router = APIRouter()

# --- In-memory storage (no database needed for demo) ---
agent_registry: dict[str, Agent] = {}
message_logs: list[LogEntry] = []

# -------------------------------------------------------
# REGISTRATION
# Developers call this to register their agent
# -------------------------------------------------------
@router.post("/agents/register")
async def register_agent(registration: AgentRegistration):
    agent_id = str(uuid.uuid4())  # generate unique ID for the agent
    agent = Agent(
        agent_id=agent_id,
        username=registration.username,
        description=registration.description,
        endpoint_url=registration.endpoint_url,
        capabilities=registration.capabilities,
        skills=registration.skills,
        community=registration.community,
        approved=False,
        registered_at=datetime.utcnow().isoformat()
    )
    agent_registry[agent_id] = agent
    return {
        "message": "Agent registered successfully. Awaiting approval.",
        "agent_id": agent_id
    }

# -------------------------------------------------------
# APPROVAL
# Admin calls this to approve a registered agent
# -------------------------------------------------------
@router.post("/agents/{agent_id}/approve")
async def approve_agent(agent_id: str):
    if agent_id not in agent_registry:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent_registry[agent_id].approved = True
    return {"message": f"Agent {agent_id} approved successfully"}

# -------------------------------------------------------
# DISCOVERY
# Agents call this to find other agents
# -------------------------------------------------------
@router.get("/agents/discover")
async def discover_agents(
    community: str = None,
    skill: str = None,
    capability: str = None
):
    results = [a for a in agent_registry.values() if a.approved]

    if community:
        results = [a for a in results if a.community == community]
    if skill:
        results = [a for a in results if skill in a.skills]
    if capability:
        results = [a for a in results if capability in a.capabilities]

    return {"agents": results}

# -------------------------------------------------------
# LIST ALL AGENTS (admin view)
# -------------------------------------------------------
@router.get("/agents")
async def list_agents():
    return {"agents": list(agent_registry.values())}

# -------------------------------------------------------
# MESSAGE ROUTING
# Agent A sends a message → coordinator forwards it to Agent B
# -------------------------------------------------------
@router.post("/messages/send")
async def send_message(message: MessageRequest):
    # Verify sending agent exists and is approved
    if message.from_agent_id not in agent_registry:
        raise HTTPException(status_code=404, detail="Sending agent not found")
    if not agent_registry[message.from_agent_id].approved:
        raise HTTPException(status_code=403, detail="Sending agent not approved")

    # Verify receiving agent exists and is approved
    if message.to_agent_id not in agent_registry:
        raise HTTPException(status_code=404, detail="Destination agent not found")
    if not agent_registry[message.to_agent_id].approved:
        raise HTTPException(status_code=403, detail="Destination agent not approved")

    # Get destination agent's endpoint
    destination = agent_registry[message.to_agent_id]

    # Log the request
    log = LogEntry(
        timestamp=datetime.utcnow().isoformat(),
        from_agent_id=message.from_agent_id,
        to_agent_id=message.to_agent_id,
        task_description=message.task_description,
        status="pending"
    )

    # Forward the message to the destination agent
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{destination.endpoint_url}/a2a/task",
                json={
                    "from_agent_id": message.from_agent_id,
                    "task_description": message.task_description,
                    "payload": message.payload
                }
            )
        log.status = "delivered"
        message_logs.append(log)
        return {
            "status": "delivered",
            "response": response.json()
        }
    except Exception as e:
        log.status = "failed"
        message_logs.append(log)
        raise HTTPException(status_code=502, detail=f"Failed to reach destination agent: {str(e)}")

# -------------------------------------------------------
# LOGS (admin view)
# -------------------------------------------------------
@router.get("/logs")
async def get_logs():
    return {"logs": message_logs}