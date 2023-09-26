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

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT \"num_red_ml\" FROM global_inventory"))
        for row in result:
            print(row[0])
    
    # if there is at least 100ml of red
    amount = 0
    if row[0] >= 100:
        amount = row[0] % 100
        ml = row[0] - (amount * 100)

        with db.engine.begin() as connection:
            result = connection.execute(sqlalchemy.text("SELECT \"num_red_potions\" FROM global_inventory"))
            for row in result:
                print(row[0])

        potions = row[0] + amount

        with db.engine.begin() as connection:
            result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET \"num_red_ml\" = {ml}, \"num_red_potions\" = {potions}"))

    return [
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": amount,
            }
        ]
