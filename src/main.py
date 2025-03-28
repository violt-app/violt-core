from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Violt Core": "FastAPI backend is running!"}
