from datetime import datetime, timedelta
from typing import Annotated, Optional, Literal


from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from fastapi.routing import APIRouter

from sqlmodel import select, or_
from sqlmodel.sql import _expression_select_cls as sql_types

from pydantic import BaseModel


from database import User, SessionDep, Entry

from auth import get_current_active_user
from voltaic import VOLTAIC

class BenchmarkResponse(BaseModel):
    entries: list[Entry]
    thresholds: dict[str, tuple[int, int, int, int]]
    energy_thresholds: tuple[int, int, int, int]

# ----------------------------------------- ENDPOINTS -----------------------------------------

entry_router = APIRouter(prefix="/entry", tags=["Entry"])

@entry_router.get("/me/vt-s{season}-{difficulty}/{date_query}")
async def read_own_entries(
        season: int,
        difficulty: Literal["novice", "intermediate", "advanced"],
        current_user: Annotated[User, Depends(get_current_active_user)],
        session: SessionDep,
        date_query: Optional[str],
    ) -> BenchmarkResponse:

    s = VOLTAIC.get(season)
    if s is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Season {season} not found.")
    
    thresholds = s.get(difficulty)
    if thresholds is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Difficulty {difficulty} not found.")

    base_query = select(Entry).where(Entry.user_id == current_user.id).where(or_(Entry.hash == hash for hash in thresholds.keys()))
    query = parse_date_query(date_query, base_query)
    entries = session.exec(query).all()
    if difficulty == "novice":
        energy_thresholds = 100, 200, 300, 400
    elif difficulty == "intermediate":
        energy_thresholds = 500, 600, 700, 800
    elif difficulty == "advanced":
        energy_thresholds = 900, 1000, 1100, 1200
    return BenchmarkResponse(entries=entries, thresholds=thresholds, energy_thresholds=energy_thresholds)

def parse_date_query(date_query: Optional[str], base_query: sql_types.SelectOfScalar) -> sql_types.SelectOfScalar:
    if date_query is None or date_query == "all":
        return base_query
    dates = date_query.split("..")
    n_dates = len(dates)
    if n_dates > 2:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="You can only specify up to two dates - a starting date and an ending date.")

    dates_ = []
    if n_dates == 1:
        dates_.append(datetime.strptime(dates[0], "%d-%m-%Y"))
        dates_.append(datetime.strptime(dates[0], "%d-%m-%Y") + timedelta(days=1))
    else:
        for date in dates:
            if date == "" and len(dates_) == 0:
                dates_.append(datetime(year=2005, month=1, day=1))
                continue
            if date == "" and len(dates_) == 1:
                dates_.append(datetime.now() + timedelta(days=1))
                continue
            dates_.append(datetime.strptime(date, "%d-%m-%Y"))

    dates = [str(int(date.timestamp())*1_000_000_000) for date in dates_]
    return base_query.where(Entry.ctime >= dates[0]).where(Entry.ctime <= dates[1])

