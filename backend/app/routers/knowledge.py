import json
import os

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import KNOWLEDGE_FILES_DIR
from app.core.exceptions import AppException
from app.core.security import get_current_user
from app.database.database import get_db
from app.database.models import User
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.knowledge_embedding import KnowledgeEmbedding
from app.models.knowledge_file import KnowledgeFile
from app.rag.faiss_store import build_index as build_faiss_index
from app.rag.faiss_store import index_exists, index_size, load_index
from app.rag.retriever import retrieve_context
from app.services.document_service import parse_document, split_documents
from app.services.embedding_service import generate_embedding

router = APIRouter(prefix="/api/knowledge", tags=["知识库"])

ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}
MAX_FILE_SIZE = 50 * 1024 * 1024


class UploadResponse(BaseModel):
    success: bool
    filename: str
    message: str


class FileItem(BaseModel):
    id: int
    filename: str
    file_type: str
    upload_time: str
    status: str


class ChunkItem(BaseModel):
    id: int
    chunk_index: int
    content: str


class EmbeddingStatusResponse(BaseModel):
    file_id: int
    total_chunks: int
    embedded_chunks: int
    status: str


class RagTestResponse(BaseModel):
    question: str
    context: str
    chunks: list


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise AppException(f"不支持的文件格式: {ext}", status_code=400)

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise AppException("文件大小不能超过 50MB", status_code=400)

    os.makedirs(KNOWLEDGE_FILES_DIR, exist_ok=True)

    file_type = ext.lstrip(".")
    filepath = os.path.join(KNOWLEDGE_FILES_DIR, file.filename)
    with open(filepath, "wb") as f:
        f.write(content)

    record = KnowledgeFile(
        filename=file.filename,
        filepath=filepath,
        file_type=file_type,
        status="uploaded",
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    try:
        docs = parse_document(filepath, file_type)
        chunks = split_documents(docs)
        for idx, chunk in enumerate(chunks):
            db.add(KnowledgeChunk(
                file_id=record.id,
                content=chunk.page_content,
                chunk_index=idx,
            ))
        record.status = "parsed"
        db.commit()
    except Exception as e:
        record.status = "parse_failed"
        db.commit()
        raise AppException(f"文件解析失败: {str(e)}", status_code=400)

    try:
        chunk_records = (
            db.query(KnowledgeChunk)
            .filter(KnowledgeChunk.file_id == record.id)
            .order_by(KnowledgeChunk.chunk_index.asc())
            .all()
        )
        for cr in chunk_records:
            vector = generate_embedding(cr.content)
            db.add(KnowledgeEmbedding(
                chunk_id=cr.id,
                embedding=json.dumps(vector),
                dimension=len(vector),
            ))
        record.status = "embedded"
        db.commit()
        build_faiss_index()
    except Exception as e:
        db.commit()
        raise AppException(f"向量化失败: {str(e)}", status_code=400)

    return UploadResponse(
        success=True,
        filename=file.filename,
        message="上传成功",
    )


@router.get("/list", response_model=list[FileItem])
def list_files(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    files = (
        db.query(KnowledgeFile)
        .order_by(KnowledgeFile.upload_time.desc())
        .all()
    )
    return [
        FileItem(
            id=f.id,
            filename=f.filename,
            file_type=f.file_type,
            upload_time=f.upload_time.isoformat(),
            status=f.status,
        )
        for f in files
    ]


@router.get("/chunks/{file_id}", response_model=list[ChunkItem])
def list_chunks(
    file_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    file_record = db.query(KnowledgeFile).filter(KnowledgeFile.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="文件不存在")

    chunks = (
        db.query(KnowledgeChunk)
        .filter(KnowledgeChunk.file_id == file_id)
        .order_by(KnowledgeChunk.chunk_index.asc())
        .all()
    )
    return [
        ChunkItem(
            id=c.id,
            chunk_index=c.chunk_index,
            content=c.content,
        )
        for c in chunks
    ]


@router.get("/embedding/status/{file_id}", response_model=EmbeddingStatusResponse)
def embedding_status(
    file_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    file_record = db.query(KnowledgeFile).filter(KnowledgeFile.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="文件不存在")

    total_chunks = (
        db.query(KnowledgeChunk)
        .filter(KnowledgeChunk.file_id == file_id)
        .count()
    )
    embedded_chunks = (
        db.query(KnowledgeEmbedding)
        .join(KnowledgeChunk)
        .filter(KnowledgeChunk.file_id == file_id)
        .count()
    )

    if total_chunks == 0:
        status = "no_chunks"
    elif embedded_chunks == total_chunks:
        status = "completed"
    else:
        status = "processing"

    return EmbeddingStatusResponse(
        file_id=file_id,
        total_chunks=total_chunks,
        embedded_chunks=embedded_chunks,
        status=status,
    )


@router.get("/rag/test", response_model=RagTestResponse)
def rag_test(
    question: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not load_index():
        raise HTTPException(status_code=400, detail="知识库尚未建立，请先上传知识文件或手动重建索引")

    from app.services.rag_service import get_rag_context
    context = get_rag_context(question, db)
    chunks = retrieve_context(question, db, top_k=5)
    return RagTestResponse(
        question=question,
        context=context,
        chunks=chunks,
    )


@router.post("/embedding/rebuild")
def rebuild_index(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    success = build_faiss_index()
    if not success:
        raise HTTPException(status_code=400, detail="索引重建失败：没有找到任何向量数据")
    return {
        "success": True,
        "message": "索引重建成功",
        "vector_count": index_size(),
    }


@router.delete("/{file_id}")
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    record = db.query(KnowledgeFile).filter(KnowledgeFile.id == file_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="文件不存在")
    if os.path.exists(record.filepath):
        os.remove(record.filepath)

    chunk_ids = [
        c[0] for c in
        db.query(KnowledgeChunk.id).filter(KnowledgeChunk.file_id == file_id).all()
    ]
    if chunk_ids:
        db.query(KnowledgeEmbedding).filter(
            KnowledgeEmbedding.chunk_id.in_(chunk_ids)
        ).delete(synchronize_session=False)
    db.query(KnowledgeChunk).filter(KnowledgeChunk.file_id == file_id).delete()
    db.delete(record)
    db.commit()
    return {"success": True, "message": "删除成功"}
