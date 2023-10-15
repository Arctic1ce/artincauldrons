from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth

import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    """ """
    print(barrels_delivered)

    with db.engine.begin() as connection:
        red_ml = 0
        green_ml = 0
        blue_ml = 0
        dark_ml = 0
        price = 0

        for barrel in barrels_delivered:
            ml = (barrel.ml_per_barrel * barrel.quantity)
        
            if barrel.potion_type == [1, 0, 0, 0]:
                red_ml = red_ml + ml
            elif barrel.potion_type == [0, 1, 0, 0]:
                green_ml = green_ml + ml
            elif barrel.potion_type == [0, 0, 1, 0]:
                blue_ml = blue_ml + ml
            elif barrel.potion_type == [0, 0, 0, 1]:
                dark_ml = dark_ml + ml
            else:
                raise Exception("Invalid potion type")
            
            price = price + (barrel.price * barrel.quantity)
            
        stmt = sqlalchemy.text("UPDATE global_inventory SET num_red_ml = num_red_ml+:a, num_green_ml = num_green_ml+:b, num_blue_ml = num_blue_ml+:c, num_dark_ml = num_dark_ml+:d, gold = gold-:e")
        result = connection.execute(stmt, {"a": red_ml, "b": green_ml, "c": blue_ml, "d": dark_ml, "e": price})

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    red_ml = 0
    green_ml = 0
    blue_ml = 0
    dark_ml = 0
    gold = 0
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))

        row = result.first()
        red_ml = row.num_red_ml
        green_ml = row.num_green_ml
        blue_ml = row.num_blue_ml
        dark_ml = row.num_dark_ml
        gold = row.gold
        
    color = ""
    if red_ml <= green_ml and red_ml <= blue_ml and red_ml <= dark_ml:
        color = "red"
    elif green_ml <= red_ml and green_ml <= blue_ml and green_ml <= dark_ml:
        color = "green"
    elif blue_ml <= red_ml and blue_ml <= green_ml and blue_ml <= dark_ml:
        color = "blue"
    else:
        color = "dark"
        
    cart = []
    temp_gold = gold
    for barrel in wholesale_catalog:
        if color == "red":
            if barrel.potion_type == [1, 0, 0, 0]:
                if temp_gold >= barrel.price:
                    cart.append({
                        "sku": barrel.sku,
                        "quantity": 1
                    })
                    temp_gold -= barrel.price
        elif color == "green":
            if barrel.potion_type == [0, 1, 0, 0]:
                if temp_gold >= barrel.price:
                    cart.append({
                        "sku": barrel.sku,
                        "quantity": 1
                    })
                    temp_gold -= barrel.price
        elif color == "blue":
            if barrel.potion_type == [0, 0, 1, 0]:
                if temp_gold >= barrel.price:
                    cart.append({
                        "sku": barrel.sku,
                        "quantity": 1
                    })
                    temp_gold -= barrel.price
        else:
            if barrel.potion_type == [0, 0, 0, 1]:
                if temp_gold >= barrel.price:
                    cart.append({
                        "sku": barrel.sku,
                        "quantity": 1
                    })
                    temp_gold -= barrel.price

    return cart
