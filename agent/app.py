from fastapi import FastAPI

app = FastAPI(title="Shopping Copilot Agent")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "agent"}
