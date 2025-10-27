# 임베딩 모델 및 벡터 DB 설정 변경 가이드

## 개요

이 문서는 RAG 시스템에서 사용하는 임베딩 모델과 Qdrant 벡터 DB 설정을 변경하는 방법을 설명합니다.

---

## 임베딩 모델 변경

### 1. 사용 가능한 한국어 임베딩 모델

#### 권장 모델 (Sentence Transformers)

| 모델 이름 | 벡터 차원 | 특징 | 용도 |
|----------|----------|------|------|
| `jhgan/ko-sroberta-multitask` | 768 | 기본 설정, 범용 | 일반 문서 검색 |
| `BM-K/KoSimCSE-roberta` | 768 | 의미 유사도 특화 | 의미 검색 중심 |
| `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | 384 | 다국어 지원, 경량 | 빠른 처리 필요 시 |
| `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` | 768 | 다국어 지원, 고성능 | 정확도 우선 |
| `intfloat/multilingual-e5-large` | 1024 | 최신 모델, 고성능 | 최고 정확도 필요 시 |

### 2. 모델 변경 방법

#### Step 1: 환경 변수 수정

`backend/.env` 파일에서 모델 이름 변경:

```bash
# 기존 (기본값)
EMBEDDING_MODEL=jhgan/ko-sroberta-multitask

# 변경 예시 1: 경량 모델로 변경
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

# 변경 예시 2: 고성능 모델로 변경
EMBEDDING_MODEL=intfloat/multilingual-e5-large
```

#### Step 2: Qdrant 컬렉션 재생성

**중요**: 모델을 변경하면 벡터 차원이 달라지므로 기존 컬렉션을 삭제하고 재생성해야 합니다.

```bash
# 방법 1: Backend 재시작 (자동 재생성)
docker-compose restart backend

# 방법 2: Qdrant 컬렉션 수동 삭제
curl -X DELETE http://localhost:6333/collections/documents
```

#### Step 3: 기존 문서 재업로드

모델 변경 후에는 **모든 문서를 다시 업로드**해야 합니다.

```bash
# 예시: 모든 문서 재업로드
for file in documents/*.pdf; do
  curl -X POST http://localhost:8000/api/upload/ \
    -F "file=@$file"
done
```

---

## 벡터 차원 확인 방법

### Python에서 확인

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('jhgan/ko-sroberta-multitask')
dimension = model.get_sentence_embedding_dimension()
print(f"Vector dimension: {dimension}")  # 출력: 768
```

### 현재 Qdrant 컬렉션 설정 확인

```bash
curl http://localhost:6333/collections/documents
```

**응답 예시**:
```json
{
  "result": {
    "vectors": {
      "size": 768,
      "distance": "Cosine"
    }
  }
}
```

---

## Qdrant 벡터 DB 설정 변경

### 1. 컬렉션 이름 변경

#### Step 1: 환경 변수 수정

```bash
# backend/.env
QDRANT_COLLECTION_NAME=my_custom_collection
```

#### Step 2: Backend 재시작

```bash
docker-compose restart backend
```

새로운 컬렉션이 자동으로 생성됩니다.

### 2. 유사도 측정 방식 변경

현재는 **Cosine 유사도**를 사용하지만, 다른 방식으로 변경 가능합니다.

#### 사용 가능한 Distance 타입

| Distance | 설명 | 사용 시기 |
|----------|------|-----------|
| `Cosine` | 코사인 유사도 (기본값) | 일반적인 텍스트 검색 |
| `Dot` | 내적 (Dot Product) | 정규화된 벡터 사용 시 |
| `Euclidean` | 유클리드 거리 | 절대 거리 중요 시 |

#### 변경 방법

`backend/app/services/qdrant_service.py` 파일 수정:

```python
from qdrant_client.models import Distance, VectorParams

# 기존 (Cosine)
self.client.create_collection(
    collection_name=self.collection_name,
    vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
)

# Euclidean으로 변경
self.client.create_collection(
    collection_name=self.collection_name,
    vectors_config=VectorParams(size=self.vector_size, distance=Distance.EUCLIDEAN),
)

# Dot Product로 변경
self.client.create_collection(
    collection_name=self.collection_name,
    vectors_config=VectorParams(size=self.vector_size, distance=Distance.DOT),
)
```

**변경 후**:
1. 코드 수정
2. 기존 컬렉션 삭제
3. Backend 재시작
4. 문서 재업로드

---

## 고급 설정

### 1. 검색 결과 개수 조정

#### RAG 서비스에서 Top-K 변경

`backend/app/services/rag_service.py`:

```python
async def answer_question(self, question: str, top_k: int = 3) -> Dict[str, Any]:
    # top_k 기본값 변경
    # 3 → 5로 변경하면 더 많은 문서 참조
```

#### API 호출 시 동적 지정

```bash
# 현재는 코드에서 고정값 사용
# 향후 개선: API에서 파라미터로 받기
```

### 2. 임베딩 모델 로컬 캐시 위치

Sentence Transformers는 모델을 자동으로 다운로드하여 캐시합니다.

**캐시 위치**:
- Linux/Mac: `~/.cache/torch/sentence_transformers/`
- Windows: `C:\Users\<username>\.cache\torch\sentence_transformers\`

**폐쇄망 배포 시 모델 미리 준비**:

```bash
# 인터넷 환경에서
python3 << EOF
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('jhgan/ko-sroberta-multitask')
print("Model downloaded to:", model._model_card_vars.get('model_name', 'Unknown'))
EOF

# 캐시 디렉토리 압축
tar -czf sentence_transformers_cache.tar.gz ~/.cache/torch/sentence_transformers/

# 서버에서 압축 해제
tar -xzf sentence_transformers_cache.tar.gz -C ~/
```

### 3. Qdrant 스토리지 위치 변경

Docker Compose에서 볼륨 마운트 위치 변경:

```yaml
# docker-compose.yml (예시, 현재는 Qdrant가 별도 실행 중)
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - ./qdrant_storage:/qdrant/storage  # 여기 경로 변경
```

또는 직접 실행 시:

```bash
docker run -d --name qdrant \
  -p 6333:6333 \
  -v /custom/path/qdrant_storage:/qdrant/storage \
  qdrant/qdrant:latest
```

---

## 벡터 검색 성능 최적화

### 1. 인덱스 파라미터 조정

Qdrant는 기본적으로 HNSW (Hierarchical Navigable Small World) 인덱스를 사용합니다.

`backend/app/services/qdrant_service.py`에서 설정:

```python
from qdrant_client.models import VectorParams, Distance, HnswConfigDiff

self.client.create_collection(
    collection_name=self.collection_name,
    vectors_config=VectorParams(
        size=self.vector_size,
        distance=Distance.COSINE,
        hnsw_config=HnswConfigDiff(
            m=16,              # 기본값: 16, 높이면 정확도↑ 메모리↑
            ef_construct=100,  # 기본값: 100, 높이면 빌드 느림, 검색 빠름
        )
    ),
)
```

### 2. 검색 정확도 vs 속도 조절

```python
# qdrant_service.py의 search 메서드
search_result = self.client.search(
    collection_name=self.collection_name,
    query_vector=query_vector,
    limit=limit,
    search_params={"hnsw_ef": 128}  # 기본 없음, 높이면 정확도↑ 속도↓
)
```

---

## 모델별 성능 비교 (참고)

| 모델 | 벡터 차원 | 검색 속도 | 정확도 | 메모리 사용 |
|------|----------|----------|--------|------------|
| MiniLM-L12 (384) | 384 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| ko-sroberta (768) | 768 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| mpnet-base (768) | 768 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| e5-large (1024) | 1024 | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |

**추천**:
- **일반 문서 검색**: `jhgan/ko-sroberta-multitask` (기본값)
- **빠른 응답 필요**: `paraphrase-multilingual-MiniLM-L12-v2`
- **최고 정확도 필요**: `intfloat/multilingual-e5-large`

---

## 문제 해결

### Q1: 모델 변경 후 검색 결과가 없음

**원인**: 기존 벡터와 차원이 달라서 검색 불가

**해결**:
```bash
# 1. 컬렉션 삭제
curl -X DELETE http://localhost:6333/collections/documents

# 2. Backend 재시작 (컬렉션 자동 재생성)
docker-compose restart backend

# 3. 문서 재업로드
```

### Q2: "Model not found" 에러

**원인**: 모델 이름 오타 또는 존재하지 않는 모델

**해결**:
- Hugging Face에서 모델 이름 확인: https://huggingface.co/models?library=sentence-transformers
- 정확한 모델 이름 사용

### Q3: 메모리 부족 에러

**원인**: 대형 모델 (e5-large 등) 사용 시 메모리 부족

**해결**:
```bash
# 더 작은 모델로 변경
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

### Q4: 검색 속도가 느림

**원인**: 너무 많은 문서 또는 큰 벡터 차원

**해결**:
1. 작은 차원 모델 사용 (384차원)
2. HNSW 파라미터 조정 (`hnsw_ef` 낮추기)
3. Top-K 결과 개수 줄이기

---

## 변경 체크리스트

임베딩 모델을 변경할 때 다음 체크리스트를 따르세요:

- [ ] `.env` 파일에 새 모델 이름 설정
- [ ] 새 모델의 벡터 차원 확인
- [ ] 기존 Qdrant 컬렉션 삭제
- [ ] Backend 재시작
- [ ] 컬렉션이 올바른 벡터 차원으로 생성되었는지 확인
- [ ] 모든 문서 재업로드
- [ ] 검색 테스트 수행
- [ ] 성능 및 정확도 확인

---

## 참고 자료

- Sentence Transformers 문서: https://www.sbert.net/
- Qdrant 문서: https://qdrant.tech/documentation/
- Hugging Face 모델 허브: https://huggingface.co/models?library=sentence-transformers&language=ko
