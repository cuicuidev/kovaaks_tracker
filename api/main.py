from typing import Any

from fastapi import FastAPI, Response
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
async def echo_root(request: Entry) -> Response:
    return Response(content=request.model_dump_json(), media_type="application/json")