from typing import Any

from fastapi import FastAPI, Request
from pydantic import BaseModel

class Entry(BaseModel):
    scenario: str
    score: float
    challenge_start: str
    sens_scale: str
    sens_increment: float
    dpi: int
    fov_scale: str
    fov: int

app = FastAPI()

@app.post("/")
async def echo_root(request: Entry) -> Entry:
    return request