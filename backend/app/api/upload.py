"""
파일 업로드 API
문서를 업로드하여 Qdrant 벡터 DB에 저장
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from datetime import datetime
import hashlib

from app.models.chat import UploadResponse
from app.services.qdrant_service import qdrant_service
from app.utils.text_extractor import TextExtractor

router = APIRouter(prefix="/api/upload", tags=["upload"])


@router.post("/", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    문서 파일을 업로드하여 벡터 DB에 저장

    지원 형식: PDF, DOCX, TXT, XLSX

    - file: 업로드할 파일
    """
    try:
        # 1. 파일에서 텍스트 추출
        file_content = await file.read()
        text = TextExtractor.extract_text(file_content, file.filename)

        if not text or len(text.strip()) < 10:
            raise HTTPException(status_code=400, detail="추출된 텍스트가 너무 짧습니다")

        # 2. 문서 ID 생성 (파일명 + 타임스탬프 해시)
        doc_id_raw = f"{file.filename}_{datetime.now().isoformat()}"
        doc_id = hashlib.md5(doc_id_raw.encode()).hexdigest()

        # 3. 메타데이터 구성
        metadata = {
            "filename": file.filename,
            "upload_time": datetime.now().isoformat(),
            "file_size": len(file_content),
        }

        # 4. Qdrant에 저장
        qdrant_service.add_document(
            doc_id=doc_id,
            text=text,
            metadata=metadata
        )

        return UploadResponse(
            message="파일이 성공적으로 업로드되었습니다",
            filename=file.filename,
            doc_id=doc_id,
            text_length=len(text)
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 업로드 실패: {str(e)}")


@router.get("/stats")
async def get_upload_stats():
    """업로드된 문서 통계"""
    try:
        count = qdrant_service.count_documents()
        return {
            "total_documents": count,
            "collection_name": qdrant_service.collection_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")
