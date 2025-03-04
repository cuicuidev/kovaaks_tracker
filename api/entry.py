from datetime import datetime, timedelta
from typing import Annotated, Optional, Literal


from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from fastapi.routing import APIRouter

from sqlmodel import select, or_
from sqlmodel.sql import _expression_select_cls as sql_types


from database import User, SessionDep, Entry

from auth import get_current_active_user

# ----------------------------------------- CONSTANTS -----------------------------------------

VOLTAIC = {
    5 : {
        "intermediate" : [
            "830238e82c367ad2ba40df1da9968131", # PASU
            "86f9526f57828ad981f6c93b35811f94", # POPCORN
            "37975ba4bbbd5f9c593e7dbd72794baa", # 1W3TS
            "5c7668cf07b550bb2b7956f5709cf84e", # WW5T
            "ec8acdea37fa767767d705e389db1463", # FROGTAGON
            "47124ba125c1807fc7deb011c2f545a7", # FLOATING HEADS
            "b11e423dba738357ce774a01422e9d91", # PGT
            "ff38084d283c4e285150faee9c6b2832", # SNAKE TRACK
            "c4c11bf8a727b6e6c836138535bd0879", # AETHER
            "489b27e681807e0212eef50241bb0769", # GROUND
            "865d54422da5368dc290d1bbc2b9b566", # RAW CONTROL
            "a5fa9fbc3d55851b11534c60b85a9247", # CONTROLSPHERE
            "dfb397975f6fcec5bd2ebf3cd0b7a66a", # DOT TS
            "03d6156260b1b2b7893b746354b889c2", # EDDIE TS
            "ff777f42a21d6ddcf8791caf2821a2bd", # DRIFT TS
            "138c732d61151697949af4a3f51311fa", # FLY TS
            "e3b4fdab121562a8d4c8c2ac426c890c", # CONTROL TS
            "7cd5eee66632ebec0c33218d218ebf95", # PENTA BOUNCE
        ],
    }
}

# ----------------------------------------- ENDPOINTS -----------------------------------------

entry_router = APIRouter(prefix="/entry", tags=["Entry"])

@entry_router.get("/me/vt-s{season}-{difficulty}/{date_query}")
async def read_own_entries(
        season: int,
        difficulty: Literal["novice", "intermediate", "advanced"],
        current_user: Annotated[User, Depends(get_current_active_user)],
        session: SessionDep,
        date_query: Optional[str],
    ) -> list[Entry]:

    s = VOLTAIC.get(season)
    if s is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Season {season} not found.")
    
    d = s.get(difficulty)
    if d is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Difficulty {difficulty} not found.")

    base_query = select(Entry).where(Entry.user_id == current_user.id).where(or_(Entry.hash == hash for hash in d))
    query = parse_date_query(date_query, base_query)
    return session.exec(query).all()

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

