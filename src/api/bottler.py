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

    red_potions = 0
    green_potions = 0
    blue_potions = 0
    red_ml = 0
    green_ml = 0
    blue_ml = 0
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))

        row = result.first()
        red_potions = row.num_red_potions
        green_potions = row.num_green_potions
        blue_potions = row.num_blue_potions
        red_ml = row.num_red_ml
        green_ml = row.num_green_ml
        blue_ml = row.num_blue_ml

    list_red_ml = 0
    list_green_ml = 0
    list_blue_ml = 0
    list_red_potions = 0
    list_green_potions = 0
    list_blue_potions = 0
    for potion in potions_delivered:
        list_red_ml += (potion.potion_type[0] * potion.quantity)
        list_green_ml += (potion.potion_type[1] * potion.quantity)
        list_blue_ml += (potion.potion_type[2] * potion.quantity)
        list_red_potions += (potion.potion_type[0] * potion.quantity) / 100
        list_green_potions += (potion.potion_type[1] * potion.quantity) / 100
        list_blue_potions += (potion.potion_type[2] * potion.quantity) / 100

    red_ml = red_ml - list_red_ml
    green_ml = green_ml - list_green_ml
    blue_ml = blue_ml - list_blue_ml
    red_potions = red_potions + list_red_potions
    green_potions = green_potions + list_green_potions
    blue_potions = blue_potions + list_blue_potions

    with db.engine.begin() as connection:
        stmt = sqlalchemy.text("UPDATE global_inventory SET num_red_ml = :a, num_green_ml = :b, num_blue_ml = :c, num_red_potions = :d, num_green_potions = :e, num_blue_potions = :f")
        result = connection.execute(stmt, {"a": red_ml, "b": green_ml, "c": blue_ml, "d": red_potions, "e": green_potions, "f": blue_potions})

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
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))

        row = result.first()
        red_ml = row.num_red_ml
        green_ml = row.num_green_ml
        blue_ml = row.num_blue_ml
    
    # if there is at least 100ml of red
    amounts = [0, 0, 0]
    if red_ml >= 100:
        amounts[0] = red_ml // 100
    if green_ml >= 100:
        amounts[1] = green_ml // 100
    if blue_ml >= 100:
        amounts[2] = blue_ml // 100

    result = []
    for i in range(len(amounts)):
        if amounts[i] > 0:
            type = [0, 0, 0, 0]
            quantity = amounts[i]
            type[i] = quantity * 100
            result.append({
                "potion_type": type,
                "quantity": quantity
            })
            
    return result
