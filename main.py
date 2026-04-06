from fastapi import FastAPI
from faker import Faker
import random

app = FastAPI(
    title="Random Person API",
    description="A simple API to generate random personal details like Name, Phone, Email, and Location.",
    version="1.0.0"
)
fake = Faker()

@app.get("/")
async def root():
    return {
        "message": "Welcome to the Random Person API",
        "endpoints": {
            "/random-person": "Get random personal details",
            "/docs": "API Documentation (Swagger UI)",
            "/redoc": "API Documentation (ReDoc)"
        }
    }

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
