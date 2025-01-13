from fastapi import FastAPI

# Define your FastAPI app instance
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}