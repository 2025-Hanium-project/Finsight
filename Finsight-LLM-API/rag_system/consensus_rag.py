from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from db import get_conn
from embedding import get_embedding

router = APIRouter()

class ConsensusSearchRequest(BaseModel):
    query: str
    top_k: int = 5

class ConsensusSearchResult(BaseModel):
    id: int
    title: str
    text: str
    score: float

@router.post('/consensus/search', response_model=List[ConsensusSearchResult])
def consensus_search(req: ConsensusSearchRequest):
    query_emb = get_embedding(req.query)
    emb_str = '[' + ','.join(str(x) for x in query_emb) + ']'
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, title, text, 1 - (embedding <#> %s::vector) AS score
                FROM consensus_reports
                ORDER BY embedding <#> %s::vector ASC
                LIMIT %s
            """, (emb_str, emb_str, req.top_k))
            rows = cur.fetchall()
    return [ConsensusSearchResult(id=row[0], title=row[1], text=row[2], score=row[3]) for row in rows]
