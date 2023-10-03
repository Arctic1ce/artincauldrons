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

    for barrel in barrels_delivered:
        ml = (barrel.ml_per_barrel * barrel.quantity)

        red_ml = 0
        green_ml = 0
        blue_ml = 0
        gold = 0
        with db.engine.begin() as connection:
            result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))

            row = result.first()
            red_ml = row.num_red_ml
            green_ml = row.num_green_ml
            blue_ml = row.num_blue_ml
            gold = row.gold

        if barrel.sku == "SMALL_RED_BARREL" or barrel.sku == "MEDIUM_RED_BARREL" or barrel.sku == "LARGE_RED_BARREL":
            red_ml = red_ml + ml
        elif barrel.sku == "SMALL_GREEN_BARREL" or barrel.sku == "MEDIUM_GREEN_BARREL" or barrel.sku == "LARGE_GREEN_BARREL":
            green_ml = green_ml + ml
        else:
            blue_ml = blue_ml + ml
        
        gold = gold - (barrel.price * barrel.quantity)
            
        with db.engine.begin() as connection:
            stmt = sqlalchemy.text("UPDATE global_inventory SET num_red_ml = :a, num_green_ml = :b, num_blue_ml = :c, gold = :d")
            result = connection.execute(stmt, {"a": red_ml, "b": green_ml, "c": blue_ml, "d": gold})

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    red_potions = 0
    red_ml = 0
    green_potions = 0
    green_ml = 0
    blue_potions = 0
    blue_ml = 0
    potions = 0
    gold = 0
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))

        row = result.first()
        red_potions = row.num_red_potions
        green_potions = row.num_green_potions
        blue_potions = row.num_blue_potions
        red_ml = row.num_red_ml
        green_ml = row.num_green_ml
        blue_ml = row.num_blue_ml
        gold = row.gold
        potions = red_potions + green_potions + blue_potions
        
    color = ""
    red = red_potions + (red_ml // 100)
    green = green_potions + (green_ml // 100)
    blue = blue_potions + (blue_ml // 100)
    
    if blue < red and blue < green:
        color = "blue"
    elif green < red and green < blue:
        color = "green"
    else:
        color = "red"
        
    cart = []
    temp_gold = gold
    for barrel in wholesale_catalog:
        if color == "red":
            if barrel.sku == "LARGE_RED_BARREL" or barrel.sku == "MEDIUM_RED_BARREL" or barrel.sku == "SMALL_RED_BARREL" or barrel.sku == "TINY_RED_BARREL":
                if gold >= barrel.price:
                    cart.append({
                        "sku": barrel.sku,
                        "quantity": 1
                    })
                    temp_gold -= barrel.price
        elif color == "green":
            if barrel.sku == "LARGE_GREEN_BARREL" or barrel.sku == "MEDIUM_GREEN_BARREL" or barrel.sku == "SMALL_GREEN_BARREL" or barrel.sku == "TINY_GREEN_BARREL":
                if gold >= barrel.price:
                    cart.append({
                        "sku": barrel.sku,
                        "quantity": 1
                    })
                    temp_gold -= barrel.price
        else:
            if barrel.sku == "LARGE_BLUE_BARREL" or barrel.sku == "MEDIUM_BLUE_BARREL" or barrel.sku == "SMALL_BLUE_BARREL" or barrel.sku == "TINY_BLUE_BARREL":
                if gold >= barrel.price:
                    cart.append({
                        "sku": barrel.sku,
                        "quantity": 1
                    })
                    temp_gold -= barrel.price

    return cart
