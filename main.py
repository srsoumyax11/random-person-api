import asyncio
import httpx
from fastapi import FastAPI, HTTPException
from faker import Faker
from pydantic import BaseModel
from typing import List, Optional
from tinydb import TinyDB, Query
from contextlib import asynccontextmanager

# Database setup
db = TinyDB('db.json')
UserTable = db.table('users')

class User(BaseModel):
    id: Optional[int] = None
    name: str
    email: str
    phone: str
    location: Optional[str] = None

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
                # Ping the production URL (updated by user)
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
    description="A simple API to generate random personal details with a self-ping service and CRUD operations using TinyDB.",
    version="1.2.0",
    lifespan=lifespan
)
fake = Faker()

@app.get("/")
async def root():
    return {
        "message": "Welcome to the Random Person API",
        "endpoints": {
            "/random-person": "Get random personal details",
            "/users": "CRUD endpoints for users",
            "/health": "Health check endpoint for self-ping",
            "/docs": "API Documentation (Swagger UI)"
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

# --- CRUD Operations ---

@app.post("/users", response_model=User, tags=["CRUD"])
async def create_user(user: User):
    """
    Create a new user in the file-based database.
    """
    user_dict = user.dict()
    if user_dict['id'] is None:
        # Simple ID generation
        existing_users = UserTable.all()
        user_dict['id'] = max([u['id'] for u in existing_users], default=0) + 1
    
    UserTable.insert(user_dict)
    return user_dict

@app.get("/users", response_model=List[User], tags=["CRUD"])
async def list_users():
    """
    List all users from the file-based database.
    """
    return UserTable.all()

@app.get("/users/{user_id}", response_model=User, tags=["CRUD"])
async def get_user(user_id: int):
    """
    Get a single user by ID.
    """
    UserMatch = Query()
    user = UserTable.get(UserMatch.id == user_id)
    if user:
        return user
    raise HTTPException(status_code=404, detail="User not found")

@app.put("/users/{user_id}", response_model=User, tags=["CRUD"])
async def update_user(user_id: int, user: User):
    """
    Update a user's details.
    """
    UserMatch = Query()
    if not UserTable.contains(UserMatch.id == user_id):
        raise HTTPException(status_code=404, detail="User not found")
    
    user_dict = user.dict()
    user_dict['id'] = user_id
    UserTable.update(user_dict, UserMatch.id == user_id)
    return user_dict

@app.delete("/users/{user_id}", tags=["CRUD"])
async def delete_user(user_id: int):
    """
    Delete a user by ID.
    """
    UserMatch = Query()
    if not UserTable.contains(UserMatch.id == user_id):
        raise HTTPException(status_code=404, detail="User not found")
    
    UserTable.remove(UserMatch.id == user_id)
    return {"message": f"User {user_id} deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
