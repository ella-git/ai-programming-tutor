import logging
from apscheduler.schedulers.background import BackgroundScheduler

from app.database.database import SessionLocal
from app.database.models import ChatRoom, RoomMemory
from app.services.summary_service import summarize_room_messages

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def summarize_all_rooms():
    db = SessionLocal()
    try:
        rooms = db.query(ChatRoom).all()
        for room in rooms:
            try:
                logger.info(f"开始总结房间 {room.id} ...")
                summary = summarize_room_messages(room.id)
                memory = db.query(RoomMemory).filter(RoomMemory.room_id == room.id).first()
                if memory:
                    memory.summary = summary
                else:
                    memory = RoomMemory(room_id=room.id, summary=summary)
                    db.add(memory)
                db.commit()
                logger.info(f"房间 {room.id} 总结完成")
            except Exception as e:
                logger.error(f"房间 {room.id} 总结失败: {e}")
                db.rollback()
    finally:
        db.close()


def start_memory_summary_task():
    scheduler.add_job(
        summarize_all_rooms,
        "interval",
        minutes=20,
        id="memory_summary",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("长期记忆定时任务已启动，每20分钟执行一次")
