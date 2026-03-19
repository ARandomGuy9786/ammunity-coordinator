from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(url, key)

# -------------------------------------------------------
# AGENT OPERATIONS
# -------------------------------------------------------

def db_register_agent(agent: dict) -> dict:
    result = supabase.table("agents").insert(agent).execute()
    return result.data[0] if result.data else None

def db_get_agent(agent_id: str) -> dict:
    result = supabase.table("agents").select("*").eq("agent_id", agent_id).execute()
    return result.data[0] if result.data else None

def db_get_all_agents() -> list:
    result = supabase.table("agents").select("*").execute()
    return result.data or []

def db_approve_agent(agent_id: str) -> dict:
    result = supabase.table("agents").update({"approved": True}).eq("agent_id", agent_id).execute()
    return result.data[0] if result.data else None

def db_delete_agent(agent_id: str) -> bool:
    result = supabase.table("agents").delete().eq("agent_id", agent_id).execute()
    return True

def db_discover_agents(community: str = None, skill: str = None, capability: str = None) -> list:
    query = supabase.table("agents").select("*").eq("approved", True)
    if community:
        query = query.eq("community", community)
    result = query.execute()
    agents = result.data or []

    # Filter by skill and capability in Python since Supabase array filtering is limited
    if skill:
        agents = [a for a in agents if skill in (a.get("skills") or [])]
    if capability:
        agents = [a for a in agents if capability in (a.get("capabilities") or [])]

    return agents

# -------------------------------------------------------
# LOG OPERATIONS
# -------------------------------------------------------

def db_add_log(log: dict) -> dict:
    result = supabase.table("message_logs").insert(log).execute()
    return result.data[0] if result.data else None

def db_get_logs() -> list:
    result = supabase.table("message_logs").select("*").order("timestamp", desc=True).execute()
    return result.data or []
