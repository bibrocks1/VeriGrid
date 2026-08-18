from fastapi import FastAPI

app = FastAPI(title="VeriGrid API")

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Backend is running!"}