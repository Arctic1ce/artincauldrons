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
        # delete these queries ****
        stmt = sqlalchemy.text("UPDATE global_inventory SET num_red_ml = 0, num_green_ml = 0, num_blue_ml = 0, num_dark_ml = 0, gold = 100")
        result = connection.execute(stmt)
        stmt = sqlalchemy.text("UPDATE potions SET quantity = 0")
        result = connection.execute(stmt)

        # only keep this last query
        result = connection.execute(sqlalchemy.text("TRUNCATE cart; TRUNCATE cart_items; TRUNCATE gold_ledger_entries; TRUNCATE ml_ledger_entries; TRUNCATE potions_ledger_entries; TRUNCATE transactions"))

    return "OK"


@router.get("/shop_info/")
def get_shop_info():
    """ """

    # TODO: Change me!
    return {
        "shop_name": "SLO Ghouls",
        "shop_owner": "Artin Davari",
    }

