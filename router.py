from fastapi import APIRouter, HTTPException
from models import AgentRegistration, Agent, MessageRequest, LogEntry
from database import (
    db_register_agent, db_get_agent, db_get_all_agents,
    db_approve_agent, db_delete_agent, db_discover_agents,
    db_add_log, db_get_logs
)
from datetime import datetime
import uuid
import httpx

router = APIRouter()

# -------------------------------------------------------
# REGISTRATION
# -------------------------------------------------------
@router.post("/agents/register")
async def register_agent(registration: AgentRegistration):
    agent_id = str(uuid.uuid4())
    agent = {
        "agent_id": agent_id,
        "username": registration.username,
        "description": registration.description,
        "endpoint_url": registration.endpoint_url,
        "capabilities": registration.capabilities,
        "skills": registration.skills,
        "community": registration.community,
        "approved": False,
        "registered_at": datetime.utcnow().isoformat()
    }
    db_register_agent(agent)
    return {
        "message": "Agent registered successfully. Awaiting approval.",
        "agent_id": agent_id
    }

# -------------------------------------------------------
# APPROVAL
# -------------------------------------------------------
@router.post("/agents/{agent_id}/approve")
async def approve_agent(agent_id: str):
    agent = db_get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    db_approve_agent(agent_id)
    return {"message": f"Agent {agent_id} approved successfully"}

# -------------------------------------------------------
# DELETE
# -------------------------------------------------------
@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str):
    agent = db_get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    db_delete_agent(agent_id)
    return {"message": f"Agent {agent['username']} deleted successfully"}

# -------------------------------------------------------
# DISCOVERY
# -------------------------------------------------------
@router.get("/agents/discover")
async def discover_agents(
    community: str = None,
    skill: str = None,
    capability: str = None
):
    agents = db_discover_agents(community, skill, capability)
    return {"agents": agents}

# -------------------------------------------------------
# LIST ALL AGENTS
# -------------------------------------------------------
@router.get("/agents")
async def list_agents():
    agents = db_get_all_agents()
    return {"agents": agents}

# -------------------------------------------------------
# MESSAGE ROUTING (direct)
# -------------------------------------------------------
@router.post("/messages/send")
async def send_message(message: MessageRequest):
    from_agent = db_get_agent(message.from_agent_id)
    if not from_agent:
        raise HTTPException(status_code=404, detail="Sending agent not found")
    if not from_agent["approved"]:
        raise HTTPException(status_code=403, detail="Sending agent not approved")

    to_agent = db_get_agent(message.to_agent_id)
    if not to_agent:
        raise HTTPException(status_code=404, detail="Destination agent not found")
    if not to_agent["approved"]:
        raise HTTPException(status_code=403, detail="Destination agent not approved")

    log = {
        "from_agent_id": message.from_agent_id,
        "to_agent_id": message.to_agent_id,
        "task_description": message.task_description,
        "status": "pending"
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{to_agent['endpoint_url']}/a2a/task",
                json={
                    "from_agent_id": message.from_agent_id,
                    "task_description": message.task_description,
                    "payload": message.payload
                }
            )
        log["status"] = "delivered"
        db_add_log(log)
        return {"status": "delivered", "response": response.json()}
    except Exception as e:
        log["status"] = "failed"
        db_add_log(log)
        raise HTTPException(status_code=502, detail=f"Failed to reach destination agent: {str(e)}")

# -------------------------------------------------------
# INTELLIGENT ROUTING
# -------------------------------------------------------
@router.post("/messages/route")
async def route_message_intelligent(message: MessageRequest):
    from_agent = db_get_agent(message.from_agent_id)
    if not from_agent:
        raise HTTPException(status_code=404, detail="Sending agent not found")
    if not from_agent["approved"]:
        raise HTTPException(status_code=403, detail="Sending agent not approved")

    # Find the routing agent
    all_agents = db_get_all_agents()
    routing_agent = next(
        (a for a in all_agents if a["username"] == "routing-agent" and a["approved"]),
        None
    )

    if not routing_agent:
        raise HTTPException(status_code=503, detail="Routing agent not available")

    log = {
        "from_agent_id": message.from_agent_id,
        "to_agent_id": routing_agent["agent_id"],
        "task_description": message.task_description,
        "status": "pending"
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{routing_agent['endpoint_url']}/route",
                json={
                    "from_agent_id": message.from_agent_id,
                    "task_description": message.task_description,
                    "message": message.payload.get("message", "")
                }
            )
        log["status"] = "delivered"
        db_add_log(log)
        return response.json()
    except Exception as e:
        log["status"] = "failed"
        db_add_log(log)
        raise HTTPException(status_code=502, detail=f"Routing agent unreachable: {str(e)}")

# -------------------------------------------------------
# LOGS
# -------------------------------------------------------
@router.get("/logs")
async def get_logs():
    logs = db_get_logs()
    return {"logs": logs}
