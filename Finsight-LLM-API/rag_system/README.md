
# RAG 시스템 (rag_system) 상세 설명

이 폴더는 컨센서스 리포트 기반 RAG(Retrieval-Augmented Generation) 시스템의 FastAPI 백엔드 예시를 모듈별로 분리해 구현한 코드입니다. 벡터 임베딩, 벡터 DB 검색, API 제공 등 RAG의 핵심 구조를 실제로 적용할 수 있습니다.

---

## 전체 구조 및 동작 흐름

1. **데이터 적재**
   - 증권사 리포트 등 CSV 데이터를 임베딩 벡터와 함께 PostgreSQL(pgvector) DB에 저장
   - `data_loader.py`의 `insert_csv_to_db` 함수 또는 `load_miraeasset_consensus.py` 등 스크립트 사용

2. **임베딩 생성**
   - `embedding.py`에서 sentence-transformers 기반 임베딩 모델 로딩 (예: E5, KoBERT 등)
   - 텍스트를 벡터로 변환해 DB에 저장 및 검색에 활용

3. **API 서버 실행**
   - `main.py`에서 FastAPI 앱 실행, `/consensus/search` 등 엔드포인트 제공

4. **검색 및 응답**
   - 쿼리 입력 → 임베딩 생성 → 벡터 유사도 기반 top-k 검색 → 결과 반환

---

## 주요 파일 및 역할

- `main.py` : FastAPI 앱 엔트리포인트, 라우터 등록, 서버 실행
- `db.py` : PostgreSQL 연결 함수(get_conn), DB 접속 정보 관리
- `embedding.py` : 임베딩 모델 로딩 및 임베딩 생성 함수(get_embedding)
- `consensus_rag.py` : `/consensus/search` API 라우터, 쿼리 임베딩 생성 및 벡터 검색
- `data_loader.py` : CSV 파일을 DB로 적재하는 함수(insert_csv_to_db), ETL/최초 적재용
- `load_miraeasset_consensus.py` : 미래에셋 리포트 CSV 적재 스크립트(사용자 추가 가능)
- `requirements.txt` : 필수 Python 패키지 목록
- `__init__.py` : 패키지 인식용(비어 있음)

---

## 주요 기술 스택 및 특징

- **임베딩 모델**: sentence-transformers 기반(E5, KoBERT, KoSimCSE 등 자유롭게 교체 가능)
- **벡터 DB**: PostgreSQL + pgvector 확장(로컬/운영 환경 모두 지원)
- **API 서버**: FastAPI(비동기, 확장성 우수)
- **ETL/데이터 적재**: pandas 기반 CSV 파싱 및 DB 적재

---

## 동작 예시 및 사용법

### 1. 데이터 적재
```python
from data_loader import insert_csv_to_db
insert_csv_to_db('경로/consensus.csv', 'consensus_reports')
#load_miraeasset_consensus.py 실행
```

### 2. DB 및 테이블 생성 예시
PostgreSQL + pgvector 확장 필요
```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE consensus_reports (
    id SERIAL PRIMARY KEY,
    title TEXT,
    text TEXT,
    embedding VECTOR(768) -- 임베딩 모델에 따라 768, 1024 등으로 변경
);
```

### 3. FastAPI 서버 실행
```bash
uvicorn main:app --reload
```

### 4. 검색 API 사용 예시
POST /consensus/search
```json
{
  "query": "삼성전자 실적 전망",
  "top_k": 5
}
```
→ 임베딩 생성 후 벡터 유사도 top-k 결과 반환

---

## 확장/운영 시 참고사항

- 임베딩 모델, DB 설정, 테이블 구조는 환경에 맞게 수정
- 대용량 데이터/운영 환경에서는 비동기 처리, 배치 적재, 보안 등 추가 구현 필요
- Milvus, Weaviate 등 외부 벡터DB 연동도 유사 구조로 확장 가능
- Rerank, 하이브리드 검색, 프롬프트 엔지니어링 등 고도화 가능

---