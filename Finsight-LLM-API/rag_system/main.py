
from fastapi import FastAPI
from consensus_rag import router as consensus_router

app = FastAPI()


app.include_router(consensus_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
