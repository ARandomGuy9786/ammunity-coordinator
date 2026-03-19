from fastapi import FastAPI
from crewai import Agent, Task, Crew, LLM
import uvicorn
import os
from pathlib import Path


def load_local_env() -> None:
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")

        if key:
            os.environ.setdefault(key, value)


load_local_env()

app = FastAPI(title="CrewAI A2A Agent")

# Define the CrewAI agent
assistant = Agent(
    role="General Assistant",
    goal="Help with any task sent through the Ammunity network",
    backstory="You are a helpful AI agent connected to the Ammunity agent network. You receive tasks from other agents and complete them.",
    verbose=True,
    llm=LLM(
        model="openai/gpt-4o-mini",
        api_key=os.environ.get("OPENAI_API_KEY")
    )
)

@app.post("/a2a/task")
async def receive_task(payload: dict):
    task_description = payload.get("task_description", "No task provided")
    message = payload.get("payload", {}).get("message", "")

    # Create and run a CrewAI task
    task = Task(
        description=f"{task_description}. {message}",
        expected_output="A helpful response to the task",
        agent=assistant
    )

    crew = Crew(
        agents=[assistant],
        tasks=[task],
        verbose=True
    )

    result = crew.kickoff()

    return {
        "status": "completed",
        "agent": "crewai-agent",
        "result": str(result)
    }

@app.get("/health")
async def health():
    return {"status": "live", "agent": "crewai-agent"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
