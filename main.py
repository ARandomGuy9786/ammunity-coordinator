from fastapi import FastAPI
from router import router

# Create the FastAPI app
app = FastAPI(
    title="Ammunity Coordinator",
    description="Central coordination layer for the Ammunity agent network",
    version="0.1.0"
)

# Register all routes from router.py
app.include_router(router)

# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "live", "service": "ammunity-coordinator"}