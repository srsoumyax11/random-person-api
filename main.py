import asyncio
import httpx
from fastapi import FastAPI
from faker import Faker
from contextlib import asynccontextmanager

# Background task for self-ping
async def self_ping():
    """
    Background task that pings the /health endpoint every 10 minutes
    to keep the application awake.
    """
    await asyncio.sleep(5)  # Give the server time to start up
    async with httpx.AsyncClient() as client:
        while True:
            try:
                # Ping local health endpoint
                # Note: In production, you might want to use the actual URL
                response = await client.get("https://random-person-api.onrender.com/health")
                print(f"Self-ping successful: {response.status_code}")
            except Exception as e:
                print(f"Self-ping failed: {e}")
            
            # Wait for 10 minutes (600 seconds)
            await asyncio.sleep(600)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the self-ping background task
    ping_task = asyncio.create_task(self_ping())
    yield
    # Cleanup: cancel the task when shutting down
    ping_task.cancel()

app = FastAPI(
    title="Random Person API",
    description="A simple API to generate random personal details with a self-ping service.",
    version="1.1.0",
    lifespan=lifespan
)
fake = Faker()

@app.get("/")
async def root():
    return {
        "message": "Welcome to the Random Person API",
        "endpoints": {
            "/random-person": "Get random personal details",
            "/health": "Health check endpoint for self-ping",
            "/docs": "API Documentation (Swagger UI)",
            "/redoc": "API Documentation (ReDoc)"
        }
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint used by the self-ping service.
    """
    return {"status": "ok"}

@app.get("/random-person")
async def get_random_person():
    """
    Returns random personal details: Name, Phone, Email, and Location.
    """
    return {
        "name": fake.name(),
        "phone": fake.phone_number(),
        "email": fake.email(),
        "location": {
            "address": fake.address().replace("\n", ", "),
            "city": fake.city(),
            "country": fake.country(),
            "latitude": float(fake.latitude()),
            "longitude": float(fake.longitude())
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
