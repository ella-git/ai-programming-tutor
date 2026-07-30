from apscheduler.schedulers.background import BackgroundScheduler

from app.database.database import SessionLocal
from app.database.models import ChatRoom
from app.services.memory_service import MemoryService
from app.services.summary_service import summarize_room_messages

scheduler = BackgroundScheduler()


def _run_summary():
    db = SessionLocal()
    try:
        rooms = db.query(ChatRoom).all()
        for room in rooms:
            summary = summarize_room_messages(room.id)
            if not summary:
                continue
            service = MemoryService(db)
            service.update_room_memory(room.id, summary)
    finally:
        db.close()


def start_memory_summary_task():
    scheduler.add_job(_run_summary, "interval", minutes=20, id="memory_summary")
    scheduler.start()
