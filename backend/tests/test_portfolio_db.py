"""RED→GREEN: build_portfolio_response arricchisce la posizione con la squadra fantasy."""
from __future__ import annotations

from bson import ObjectId

from app.models.common import utc_now
from app.modules.portfolio.service import build_portfolio_response


async def test_portfolio_position_includes_team_fantasy_name(mock_db):
    uid = ObjectId()
    tid = ObjectId()
    aid = ObjectId()
    now = utc_now()

    await mock_db.user_wallets.insert_one(
        {"user_id": uid, "balance_credits": 100.0, "updated_at": now}
    )
    await mock_db.teams_fantasy.insert_one({
        "_id": tid, "sport_id": "calcio", "fantasy_name": "Nerazzurri Milano",
        "color_primary": "#003399",
    })
    await mock_db.athletes.insert_one({
        "_id": aid, "sport_id": "calcio", "status": "ACTIVE", "role": "ATT",
        "display_label": "L. Test", "team_fantasy_id": tid,
        "prezzo_corrente_crediti": 0.02, "prezzo_iniziale_crediti": 0.02,
    })
    await mock_db.holdings.insert_one({
        "user_id": uid, "athlete_id": aid, "quantity": 100,
        "lots": [{"qty": 100, "price": 0.018, "acquired_at": now}],
    })

    resp = await build_portfolio_response(mock_db, uid)
    pos = resp["positions"][0]
    assert pos["team_fantasy_name"] == "Nerazzurri Milano"
    assert pos["team_color_primary"] == "#003399"
