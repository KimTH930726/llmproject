# Few-shot & Intent 관리 기능 가이드

## 📋 개요

Few-shot 학습과 Intent 분류를 관리하기 위한 CRUD 기능이 추가되었습니다.

### 주요 기능
1. **Intent 관리** - 쿼리 의도 분류 (rag_search, sql_query, general 등)
2. **Few-shot 관리** - Few-shot 학습 예제 추가/수정/삭제
3. **원문 질의 관리** - Few-shot으로 변환하기 전 원본 쿼리 기록
4. **Audit 로그** - Few-shot 변경 이력 자동 기록 (INSERT, UPDATE, DELETE)

---

## 🗄️ 데이터베이스 스키마

### 1. `intents` 테이블
쿼리 의도 분류 관리

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | SERIAL | Primary Key |
| name | VARCHAR(100) | 의도 이름 (unique) |
| description | VARCHAR(500) | 의도 설명 |
| created_at | TIMESTAMP | 생성 시각 |
| updated_at | TIMESTAMP | 수정 시각 |

**기본 데이터:**
- `rag_search` - RAG 벡터 검색
- `sql_query` - 자연어 SQL 변환
- `general` - 일반 대화

### 2. `few_shots` 테이블
Few-shot 학습 예제 관리

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | SERIAL | Primary Key |
| intent_id | INTEGER | FK → intents.id |
| user_query | TEXT | 사용자 질의 예제 |
| expected_response | TEXT | 예상 응답 |
| is_active | BOOLEAN | 활성화 여부 |
| created_at | TIMESTAMP | 생성 시각 |
| updated_at | TIMESTAMP | 수정 시각 (트리거로 자동 업데이트) |

### 3. `few_shot_queries` 테이블
원문 질의 기록 (Few-shot으로 변환 전)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | SERIAL | Primary Key |
| few_shot_id | INTEGER | FK → few_shots.id (nullable) |
| query_text | TEXT | 원문 질의 텍스트 |
| detected_intent | VARCHAR(100) | 감지된 의도 |
| is_converted | BOOLEAN | Few-shot 변환 여부 |
| created_at | TIMESTAMP | 생성 시각 |

### 4. `few_shot_audit` 테이블
Few-shot 변경 이력 (자동 기록)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | SERIAL | Primary Key |
| few_shot_id | INTEGER | FK → few_shots.id |
| action | VARCHAR(20) | INSERT, UPDATE, DELETE |
| old_value | JSONB | 변경 전 값 |
| new_value | JSONB | 변경 후 값 |
| changed_by | VARCHAR(100) | 변경자 (기본값: system) |
| created_at | TIMESTAMP | 생성 시각 |

**트리거:** `few_shots` 테이블의 INSERT/UPDATE/DELETE 시 자동으로 audit 테이블에 기록

---

## 🚀 배포 및 실행

### 1. 데이터베이스 마이그레이션

**방법 1: docker-compose.dev.yml 사용 (권장)**
```bash
# 전체 스택 재시작 (init.sql 자동 실행)
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d

# PostgreSQL 초기화 확인
docker exec postgres psql -U admin -d applicants_db -c "\dt"
```

**방법 2: 기존 DB에 수동 마이그레이션**
```bash
# migrations/ 디렉토리의 SQL 실행
docker exec -i postgres psql -U admin -d applicants_db < migrations/001_create_fewshot_tables.sql

# 또는
psql -U admin -d applicants_db -f migrations/001_create_fewshot_tables.sql
```

### 2. 백엔드 실행

```bash
cd backend

# 의존성 확인 (requirements.txt에 이미 포함됨)
pip install -r requirements.txt

# 개발 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**또는 Docker:**
```bash
docker-compose -f docker-compose.dev.yml restart backend
```

### 3. 프론트엔드 실행

```bash
cd frontend

# 환경 변수 설정
cp .env.example .env
# .env 파일 확인: VITE_API_BASE_URL=http://localhost:8000

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

**또는 Docker:**
```bash
docker-compose -f docker-compose.dev.yml restart frontend
```

### 4. 접속

- **Frontend**: http://localhost (또는 http://localhost:5173 for Vite dev)
- **Backend API Docs**: http://localhost:8000/docs
- **Intent 관리**: 프론트엔드 첫 번째 탭
- **Few-shot 관리**: 프론트엔드 두 번째 탭

---

## 📡 API 엔드포인트

### Intent API (`/api/intent`)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/intent/` | 모든 Intent 목록 조회 |
| GET | `/api/intent/{id}` | 특정 Intent 조회 |
| POST | `/api/intent/` | Intent 생성 |
| PUT | `/api/intent/{id}` | Intent 수정 |
| DELETE | `/api/intent/{id}` | Intent 삭제 |

**생성 예시:**
```bash
curl -X POST http://localhost:8000/api/intent/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "data_analysis",
    "description": "데이터 분석 질의"
  }'
```

### Few-shot API (`/api/fewshot`)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/fewshot/` | 모든 Few-shot 목록 조회 (필터링 가능) |
| GET | `/api/fewshot/{id}` | 특정 Few-shot 조회 |
| POST | `/api/fewshot/` | Few-shot 생성 |
| PUT | `/api/fewshot/{id}` | Few-shot 수정 |
| DELETE | `/api/fewshot/{id}` | Few-shot 삭제 |

**필터링:**
- `?intent_id=1` - Intent ID로 필터링
- `?is_active=true` - 활성화 상태로 필터링

**생성 예시:**
```bash
curl -X POST http://localhost:8000/api/fewshot/ \
  -H "Content-Type: application/json" \
  -d '{
    "intent_id": 1,
    "user_query": "지원자 1번의 경력은?",
    "expected_response": "5년간 백엔드 개발 경력을 쌓았습니다...",
    "is_active": true
  }'
```

### Few-shot Query API (`/api/fewshot/queries`)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/fewshot/queries/` | 모든 Query 목록 조회 (필터링 가능) |
| GET | `/api/fewshot/queries/{id}` | 특정 Query 조회 |
| POST | `/api/fewshot/queries/` | Query 생성 |
| PUT | `/api/fewshot/queries/{id}` | Query 수정 (few_shot_id 연결) |
| DELETE | `/api/fewshot/queries/{id}` | Query 삭제 |

**필터링:**
- `?is_converted=false` - 미변환 Query만 조회
- `?limit=50` - 최대 결과 수 제한

**생성 예시:**
```bash
curl -X POST http://localhost:8000/api/fewshot/queries/ \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "사용자가 입력한 원문 질의",
    "detected_intent": "rag_search",
    "is_converted": false
  }'
```

### Few-shot Audit API (`/api/fewshot/audit`)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/fewshot/audit/` | 모든 Audit 이력 조회 |
| GET | `/api/fewshot/audit/{few_shot_id}` | 특정 Few-shot의 Audit 이력 |

**필터링:**
- `?action=UPDATE` - UPDATE 작업만 조회
- `?limit=100` - 최대 결과 수 제한

**조회 예시:**
```bash
# 특정 Few-shot의 변경 이력
curl http://localhost:8000/api/fewshot/audit/1

# 모든 DELETE 작업 이력
curl http://localhost:8000/api/fewshot/audit/?action=DELETE
```

---

## 🎨 프론트엔드 사용법

### Intent 관리 탭

1. **Intent 목록 보기**
   - 페이지 로드 시 자동으로 모든 Intent 표시
   - 각 Intent의 이름, 설명, 생성/수정 시각 확인

2. **Intent 추가**
   - "+ 새 Intent" 버튼 클릭
   - 이름 (필수) 및 설명 입력
   - "생성" 버튼 클릭

3. **Intent 수정**
   - 목록에서 "수정" 버튼 클릭
   - 내용 변경 후 "수정" 버튼 클릭

4. **Intent 삭제**
   - 목록에서 "삭제" 버튼 클릭
   - 확인 다이얼로그에서 "확인"

### Few-shot 관리 탭

**3개의 하위 탭:**
1. **Few-shot 예제** - 학습 예제 관리
2. **원문 질의** - 원본 쿼리 기록
3. **변경 이력** - Audit 로그

#### Few-shot 예제 탭

1. **Intent로 필터링**
   - 상단 드롭다운에서 Intent 선택
   - 자동으로 해당 Intent의 Few-shot만 표시

2. **Few-shot 추가**
   - "+ 새 Few-shot" 버튼 클릭
   - Intent 선택 (선택사항)
   - 사용자 질의 (필수) 입력
   - 예상 응답 입력 (선택사항)
   - 활성화 체크박스 선택
   - "생성" 버튼 클릭

3. **Few-shot 수정**
   - 목록에서 "수정" 버튼 클릭
   - 내용 변경 후 "수정" 버튼 클릭

4. **Few-shot 삭제**
   - 목록에서 "삭제" 버튼 클릭
   - 확인 다이얼로그에서 "확인"
   - **자동으로 Audit 테이블에 DELETE 로그 기록됨**

#### 원문 질의 탭

1. **Query 목록 보기**
   - 최근 100개 Query 표시
   - 질의 텍스트, 감지된 Intent, 변환 여부 확인

2. **Query 삭제**
   - 목록에서 "삭제" 버튼 클릭

#### 변경 이력 탭

1. **Few-shot ID로 필터링**
   - 입력 필드에 Few-shot ID 입력
   - 해당 Few-shot의 변경 이력만 표시

2. **이력 확인**
   - INSERT (녹색) - 생성 이력
   - UPDATE (노란색) - 수정 이력
   - DELETE (빨간색) - 삭제 이력

---

## 🧪 테스트 시나리오

### 시나리오 1: Intent 추가 및 Few-shot 생성

```bash
# 1. Intent 추가
curl -X POST http://localhost:8000/api/intent/ \
  -H "Content-Type: application/json" \
  -d '{"name": "test_intent", "description": "테스트용 Intent"}'

# 2. Few-shot 추가 (intent_id를 1번에서 받은 ID로 변경)
curl -X POST http://localhost:8000/api/fewshot/ \
  -H "Content-Type: application/json" \
  -d '{
    "intent_id": 4,
    "user_query": "테스트 질의입니다",
    "expected_response": "테스트 응답입니다",
    "is_active": true
  }'

# 3. Few-shot 조회
curl http://localhost:8000/api/fewshot/?intent_id=4

# 4. Audit 이력 확인 (INSERT 로그가 자동으로 생성됨)
curl http://localhost:8000/api/fewshot/audit/
```

### 시나리오 2: Few-shot 수정 및 Audit 확인

```bash
# 1. Few-shot 수정
curl -X PUT http://localhost:8000/api/fewshot/1 \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "수정된 질의입니다",
    "is_active": false
  }'

# 2. Audit 이력 확인 (UPDATE 로그가 자동으로 생성됨)
curl http://localhost:8000/api/fewshot/audit/1
```

### 시나리오 3: Few-shot Query 생성 및 변환

```bash
# 1. Query 생성
curl -X POST http://localhost:8000/api/fewshot/queries/ \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "지원자 정보를 알려주세요",
    "detected_intent": "sql_query",
    "is_converted": false
  }'

# 2. 미변환 Query 조회
curl http://localhost:8000/api/fewshot/queries/?is_converted=false

# 3. Query를 Few-shot으로 변환 (few_shot_id 연결)
curl -X PUT http://localhost:8000/api/fewshot/queries/1 \
  -H "Content-Type: application/json" \
  -d '{
    "few_shot_id": 1,
    "is_converted": true
  }'
```

---

## 🔧 문제 해결

### 1. 테이블이 생성되지 않았다면

```bash
# 수동으로 마이그레이션 실행
docker exec -i postgres psql -U admin -d applicants_db < migrations/001_create_fewshot_tables.sql

# 테이블 확인
docker exec postgres psql -U admin -d applicants_db -c "\dt"
```

### 2. 프론트엔드에서 API 호출 실패

```bash
# CORS 에러: backend/app/main.py의 allow_origins 확인
# 환경 변수 확인
docker exec backend env | grep VITE_API_BASE_URL

# frontend/.env 파일 확인
cat frontend/.env
```

### 3. Audit 로그가 생성되지 않는다면

```bash
# 트리거 확인
docker exec postgres psql -U admin -d applicants_db -c "\df"

# 트리거 재생성
docker exec -i postgres psql -U admin -d applicants_db < migrations/001_create_fewshot_tables.sql
```

### 4. 백엔드 에러

```bash
# 로그 확인
docker-compose -f docker-compose.dev.yml logs -f backend

# SQLModel 모델 임포트 확인
docker exec backend python -c "from app.models.few_shot import Intent, FewShot"
```

---

## 📊 주요 특징

### 자동 Audit 로깅
- Few-shot 테이블의 모든 변경사항이 자동으로 기록됨
- PostgreSQL 트리거를 사용하여 INSERT/UPDATE/DELETE 시 자동 실행
- 변경 전/후 값을 JSON 형식으로 저장

### Intent 기반 필터링
- Few-shot 목록을 Intent별로 필터링 가능
- 각 Few-shot에 Intent를 연결하여 분류 관리

### Few-shot Query 변환 추적
- 원문 질의를 저장하고 Few-shot으로 변환했는지 추적
- 변환 상태(is_converted) 플래그로 관리

### 활성화 상태 관리
- Few-shot을 비활성화하여 학습에서 제외 가능
- 삭제하지 않고도 임시로 사용 중지 가능

---

## 🎯 다음 단계

1. **Few-shot 활용**: QueryRouter나 RAG 서비스에서 Few-shot 데이터 활용
2. **Intent 학습**: Intent 분류 모델 학습을 위한 데이터 수집
3. **Query 수집**: 실제 사용자 질의를 Few-shot Query로 자동 저장
4. **Audit 분석**: 변경 이력을 분석하여 Few-shot 품질 개선

---

## 📝 관련 파일

### Backend
- `backend/app/models/few_shot.py` - SQLModel 모델 정의
- `backend/app/api/intent.py` - Intent CRUD API
- `backend/app/api/fewshot.py` - Few-shot CRUD API
- `backend/app/main.py` - 라우터 등록
- `migrations/001_create_fewshot_tables.sql` - 마이그레이션 SQL (독립 실행용)
- `init.sql` - 초기화 스크립트 (Docker Compose용, 마이그레이션 포함)

### Frontend
- `frontend/src/components/IntentManagement.tsx` - Intent 관리 컴포넌트
- `frontend/src/components/FewShotManagement.tsx` - Few-shot 관리 컴포넌트
- `frontend/src/App.tsx` - 메인 앱 (탭 네비게이션)
- `frontend/.env.example` - 환경 변수 템플릿

---

이제 Intent와 Few-shot을 웹 UI에서 직접 관리할 수 있습니다! 🎉
