from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Define your FastAPI app instance
app = FastAPI()

# Enable CORS for the frontend URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server for Preact
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}