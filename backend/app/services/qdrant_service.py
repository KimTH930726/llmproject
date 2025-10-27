"""
Qdrant 벡터 데이터베이스 연동 서비스
문서 임베딩 저장 및 검색 기능 제공
"""
import os
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()


class QdrantService:
    """Qdrant 벡터 DB와 임베딩 모델을 관리하는 서비스"""

    def __init__(self):
        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.collection_name = os.getenv("QDRANT_COLLECTION_NAME", "documents")
        self.embedding_model_name = os.getenv("EMBEDDING_MODEL", "jhgan/ko-sroberta-multitask")

        # Qdrant 클라이언트 초기화
        self.client = QdrantClient(url=self.qdrant_url)

        # 임베딩 모델 로드 (한국어 지원 모델)
        self.embedding_model = SentenceTransformer(self.embedding_model_name)
        self.vector_size = self.embedding_model.get_sentence_embedding_dimension()

        # 컬렉션 생성 (없는 경우)
        self._ensure_collection()

    def _ensure_collection(self):
        """컬렉션이 없으면 생성"""
        collections = self.client.get_collections().collections
        collection_names = [col.name for col in collections]

        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
            )

    def add_document(self, doc_id: str, text: str, metadata: Dict[str, Any] = None) -> None:
        """
        문서를 벡터화하여 Qdrant에 저장

        Args:
            doc_id: 문서 고유 ID
            text: 문서 텍스트
            metadata: 추가 메타데이터 (파일명, 업로드 시간 등)
        """
        # 텍스트를 임베딩 벡터로 변환
        vector = self.embedding_model.encode(text).tolist()

        # 메타데이터 기본값 설정
        payload = metadata or {}
        payload["text"] = text

        # Qdrant에 저장
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=doc_id,
                    vector=vector,
                    payload=payload
                )
            ]
        )

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        쿼리와 유사한 문서 검색

        Args:
            query: 검색 쿼리
            limit: 반환할 최대 결과 수

        Returns:
            검색 결과 리스트 (각 결과는 text, score, metadata 포함)
        """
        # 쿼리를 임베딩 벡터로 변환
        query_vector = self.embedding_model.encode(query).tolist()

        # Qdrant에서 유사 문서 검색
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit
        )

        # 결과 포맷팅
        results = []
        for hit in search_result:
            results.append({
                "text": hit.payload.get("text", ""),
                "score": hit.score,
                "metadata": {k: v for k, v in hit.payload.items() if k != "text"}
            })

        return results

    def delete_document(self, doc_id: str) -> None:
        """문서 삭제"""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=[doc_id]
        )

    def count_documents(self) -> int:
        """저장된 문서 개수 반환"""
        collection_info = self.client.get_collection(self.collection_name)
        return collection_info.points_count


# 싱글톤 인스턴스
qdrant_service = QdrantService()
