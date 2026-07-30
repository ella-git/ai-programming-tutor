from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers import auth, room, websocket, agent, memory, semantic
from app.database.database import engine, Base
from app.tasks.memory_summary_task import start_memory_summary_task, scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    start_memory_summary_task()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="AI Chat Room API", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(room.router)
app.include_router(websocket.router)
app.include_router(agent.router)
app.include_router(memory.router)
app.include_router(semantic.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
