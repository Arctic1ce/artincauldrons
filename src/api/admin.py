from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth

import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("TRUNCATE cart; TRUNCATE cart_items; TRUNCATE gold_ledger_entries; TRUNCATE ml_ledger_entries; TRUNCATE potions_ledger_entries; TRUNCATE transactions"))
        result = connection.execute(sqlalchemy.text("INSERT INTO transactions (gold) VALUES (100)"))
        result = connection.execute(sqlalchemy.text("SELECT * FROM transactions ORDER BY created_at DESC LIMIT 1"))
        row = result.first()
        transaction_id = row.id
        stmt = sqlalchemy.text("INSERT INTO gold_ledger_entries (transaction_id, change) VALUES (:a, 100)")
        result = connection.execute(stmt, {"a": transaction_id})

    return "OK"


@router.get("/shop_info/")
def get_shop_info():
    """ """

    # TODO: Change me!
    return {
        "shop_name": "SLO Ghouls",
        "shop_owner": "Artin Davari",
    }

