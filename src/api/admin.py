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
        result = connection.execute(sqlalchemy.text("SELECT * FROM potions"))
        potion_types = []
        quantities = []
        for row in result:
            potion_types.append(row.potion_type)
            quantities.append(0)
        result = connection.execute(sqlalchemy.text("INSERT INTO transactions (potion_type, quantity, red_ml, green_ml, blue_ml, dark_ml, gold) VALUES (:a, :b, 0, 0, 0, 0, 100)"), {"a": potion_types, "b": quantities})
        result = connection.execute(sqlalchemy.text("SELECT * FROM transactions ORDER BY created_at DESC LIMIT 1"))
        row = result.first()
        transaction_id = row.id
        stmt = sqlalchemy.text("INSERT INTO gold_ledger_entries (transaction_id, change) VALUES (:a, 100)")
        result = connection.execute(stmt, {"a": transaction_id})
        result = connection.execute(sqlalchemy.text("INSERT INTO ml_ledger_entries (transaction_id, color, change) VALUES (:a, \'red\', 0), (:a, \'green\', 0), (:a, \'blue\', 0), (:a, \'dark\', 0)"), {"a": transaction_id})
        for i in range(len(potion_types)):
            stmt = sqlalchemy.text("INSERT INTO potions_ledger_entries (transaction_id, potion_type, change) VALUES (:a, :b, 0)")
            result = connection.execute(stmt, {"a": transaction_id, "b": potion_types[i]})

    return "OK"


@router.get("/shop_info/")
def get_shop_info():
    """ """

    # TODO: Change me!
    return {
        "shop_name": "SLO Ghouls",
        "shop_owner": "Artin Davari",
    }

