from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth

import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    """ """
    print(potions_delivered)

    with db.engine.begin() as connection:
        red_ml = 0
        green_ml = 0
        blue_ml = 0
        dark_ml = 0

        for potion in potions_delivered:
            red_ml += (potion.potion_type[0] * potion.quantity)
            green_ml += (potion.potion_type[1] * potion.quantity)
            blue_ml += (potion.potion_type[2] * potion.quantity)
            dark_ml += (potion.potion_type[3] * potion.quantity)

            stmt = sqlalchemy.text("UPDATE potions SET quantity = quantity+:a WHERE potion_type = :b")
            result = connection.execute(stmt, {"a": potion.quantity, "b": potion.potion_type})

        stmt = sqlalchemy.text("UPDATE global_inventory SET num_red_ml = num_red_ml-:a, num_green_ml = num_green_ml-:b, num_blue_ml = num_blue_ml-:c, num_dark_ml = num_dark_ml-:d")
        result = connection.execute(stmt, {"a": red_ml, "b": green_ml, "c": blue_ml, "d": dark_ml})

    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.

    red_ml = 0
    green_ml = 0
    blue_ml = 0
    dark_ml = 0
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        row = result.first()
        red_ml = row.num_red_ml
        green_ml = row.num_green_ml
        blue_ml = row.num_blue_ml
        dark_ml = row.num_dark_ml

        mls = [red_ml, green_ml, blue_ml, dark_ml]
        results = []
        result = connection.execute(sqlalchemy.text("SELECT * FROM potions ORDER BY quantity ASC"))
        result_dict = result.mappings().all()
        for row in result_dict:
            potion_type = row["potion_type"]
            enough = True
            for i in range(len(mls)):
                if (mls[i] < potion_type[i]):
                    enough = False
                    break
            
            if enough:
                for i in range(len(mls)):
                    mls[i] -= potion_type[i]
                results.append({
                    "potion_type": potion_type,
                    "quantity": 1
                })
            
    return results
