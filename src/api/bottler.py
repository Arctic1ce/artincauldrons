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
        result = connection.execute(sqlalchemy.text("SELECT \"num_red_ml\" FROM global_inventory"))
        for row in result:
            print(row[0])
    
    red_ml = row[0]

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT \"num_red_potions\" FROM global_inventory"))
        for row in result:
            print(row[0])
    
    red_potions = row[0]

    list_red_ml = 0
    list_red_potions = 0
    for potion in potions_delivered:
        list_red_ml += (potion.potion_type[0] * potion.quantity)
        list_red_potions += potion.quantity

    ml = red_ml - list_red_ml
    potions = red_potions + list_red_potions

    with db.engine.begin() as connection:
        stmt = sqlalchemy.text("UPDATE global_inventory SET \"num_red_ml\" = :a, \"num_red_potions\" = :b")
        result = connection.execute(stmt, {"a": ml, "b": potions})

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
        amount = row[0] // 100

    return [
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": amount,
            }
        ]
