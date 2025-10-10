from fastapi import FastAPI
import uvicorn


from app.core.config import settings
from app.core.setup_cors import setup_cors
from app.api.v1.api import api_router


app = FastAPI() 

# Set CORS
setup_cors(app)

app.include_router(api_router)

@app.get("/")
def index():
    return {"message": "Welcome to Assistbot Service."}

@app.post("/")
def post_index():
    return {"error": "Method not allowed", "message": "Use GET / for API information"}

if __name__ == "__main__":
  
    if settings.RUN_ENV == "production":
        reload = False
    else:
        reload = True

    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=reload)
    #uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=reload)
