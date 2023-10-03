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
        if barrel.sku == "SMALL_RED_BARREL":
            ml = (barrel.ml_per_barrel * barrel.quantity)

            red_ml = 0
            gold = 0
            with db.engine.begin() as connection:
                result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
                for row in result:
                    red_ml = row[3]
                    gold = row[6]
            red_ml = red_ml + ml
            gold = gold - (barrel.price * barrel.quantity)
            
            with db.engine.begin() as connection:
                stmt = sqlalchemy.text("UPDATE global_inventory SET num_red_ml = :a, gold = :b")
                result = connection.execute(stmt, {"a": red_ml, "b": gold})

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    potions = 0
    gold = 0
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        for row in result:
            potions = row[0]
            gold = row[6]
            print(row[0])

    # buy a barrel if less than 10 potions
    amount = 0
    for barrel in wholesale_catalog:
        if barrel.sku == "SMALL_RED_BARREL":
            if potions < 10 and gold >= barrel.price:
                amount = 1
    
    if amount > 0:
        return [
            {
                "sku": "SMALL_RED_BARREL",
                "quantity": amount,
            }
        ]
    else:
        return []
