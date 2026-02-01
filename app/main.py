from __future__ import annotations

import csv
import io
import logging
from typing import Optional

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.db import fetch_hands, init_db, insert_hands, list_players
from app.parser.hand_parser import parse_hands
from app.stats import compute_stats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mini_pokertracker")

app = FastAPI(title="Mini PokerTracker")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    players = list_players()
    return templates.TemplateResponse(
        "index.html", {"request": request, "players": players}
    )


@app.get("/definitions", response_class=HTMLResponse)
def definitions(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("definitions.html", {"request": request})


@app.post("/upload")
async def upload(file: UploadFile = File(...)) -> RedirectResponse:
    raw_text = (await file.read()).decode("utf-8", errors="ignore")
    hands = parse_hands(raw_text)
    inserted = insert_hands(hands)
    logger.info("Inserted %s hands from %s", inserted, file.filename)
    return RedirectResponse("/", status_code=303)


@app.get("/stats")
def stats(
    player: str,
    allow_villain: bool = False,
    hero_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    game_type: Optional[str] = None,
    stakes: Optional[str] = None,
    table_size: Optional[int] = None,
) -> JSONResponse:
    if not allow_villain and hero_name and player != hero_name:
        return JSONResponse(
            {
                "error": "Villain stats are disabled. Enable them only if IDs are stable and permitted.",
            },
            status_code=400,
        )
    hands = fetch_hands(
        player_name=player,
        start_date=start_date,
        end_date=end_date,
        game_type=game_type,
        stakes=stakes,
        table_size=table_size,
    )
    stats_payload = compute_stats(hands, player)
    warning = None
    if stats_payload["hands"] < 50:
        warning = "Low sample size. HUD stats are noisy under 50 hands."
    return JSONResponse({"stats": stats_payload, "warning": warning})


@app.get("/export")
def export(
    player: str,
    format: str = "csv",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    game_type: Optional[str] = None,
    stakes: Optional[str] = None,
    table_size: Optional[int] = None,
) -> Response:
    hands = fetch_hands(
        player_name=player,
        start_date=start_date,
        end_date=end_date,
        game_type=game_type,
        stakes=stakes,
        table_size=table_size,
    )
    stats_payload = compute_stats(hands, player)

    if format == "json":
        return JSONResponse(stats_payload)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["stat", "value"])
    for key, value in stats_payload.items():
        writer.writerow([key, value])
    return Response(
        output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={player}_stats.csv"},
    )


@app.post("/reset")
def reset() -> RedirectResponse:
    from app.db import get_connection

    conn = get_connection()
    conn.execute("DELETE FROM hands")
    conn.commit()
    conn.close()
    return RedirectResponse("/", status_code=303)
