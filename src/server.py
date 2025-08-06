from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Medium MCP Server is running"}
