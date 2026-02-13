from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, Depends
from sqlmodel import SQLModel, Field, Relationship, Session, create_engine, select

DATABASE_URL = "postgresql+psycopg://banks_user:NYHC4L!fe@localhost:5432/banks_db"
engine = create_engine(DATABASE_URL, echo=False)

class Query(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    raw_q: str
    shallow: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    snippets: List["Snippet"] = Relationship(back_populates="query")

class Snippet(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    query_id: int = Field(foreign_key="query.id")
    city: str
    channel: str
    source_url: str
    title: str
    snippet_text: str
    rank: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    query: Query = Relationship(back_populates="snippets")

def get_session():
    with Session(engine) as session:
        yield session

app = FastAPI(title="BANKS")

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

@app.post("/queries", response_model=Query)
def store_query(raw_q: str, shallow: bool = False, session: Session = Depends(get_session)):
    q = Query(raw_q=raw_q, shallow=shallow)
    session.add(q)
    session.commit()
    session.refresh(q)
    return q

@app.post("/queries/{query_id}/snippets")
def store_snippets(query_id: int, snippets: list[dict], session: Session = Depends(get_session)):
    objs = [
        Snippet(
            query_id=query_id,
            city=s["city"],
            channel=s["channel"],
            source_url=s["url"],
            title=s["title"],
            snippet_text=s["snippet"],
            rank=s["rank"],
        )
        for s in snippets
    ]
    session.add_all(objs)
    session.commit()
    return {"stored": len(objs)}

@app.get("/search")
def search_banks(q: str, limit: int = 40, session: Session = Depends(get_session)):
    stmt = (
        select(Snippet)
        .where(Snippet.snippet_text.ilike(f"%{q}%"))
        .order_by(Snippet.created_at.desc(), Snippet.rank.asc())
        .limit(limit)
    )
    results = session.exec(stmt).all()
    return results
from rilie_core import RILIE
@app.post("/v1/rilie") 
def rilie_endpoint(request: dict):
    rilie = RILIE()
    return rilie.process(request["stimulus"])