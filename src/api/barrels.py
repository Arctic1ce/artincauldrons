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
            
            price += (barrel.price * barrel.quantity)
            
        price *= -1
        stmt = sqlalchemy.text("INSERT INTO transactions (red_ml, green_ml, blue_ml, dark_ml, gold) VALUES (:a, :b, :c, :d, :e)")
        result = connection.execute(stmt, {"a": red_ml, "b": green_ml, "c": blue_ml, "d": dark_ml, "e": price})

        result = connection.execute(sqlalchemy.text("SELECT * FROM transactions ORDER BY created_at DESC LIMIT 1"))
        row = result.first()
        transaction_id = row.id
        stmt = sqlalchemy.text("INSERT INTO gold_ledger_entries (transaction_id, change) VALUES (:a, :b)")
        result = connection.execute(stmt, {"a": transaction_id, "b": price})

        ml_change = [red_ml, green_ml, blue_ml, dark_ml]
        for i in range(len(ml_change)):
            color = ""
            if i == 0: color = "red"
            elif i == 1: color = "green"
            elif i == 2: color = "blue"
            else: color = "dark"
            if ml_change[i] > 0:
                stmt = sqlalchemy.text("INSERT INTO ml_ledger_entries (transaction_id, color, change) VALUES (:a, :b, :c)")
                result = connection.execute(stmt, {"a": transaction_id, "b": color, "c": ml_change[i]})

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
        result = connection.execute(sqlalchemy.text("SELECT SUM(change) AS gold FROM gold_ledger_entries"))
        gold = result.first()[0]
        result = connection.execute(sqlalchemy.text("SELECT SUM(change) AS red_ml FROM ml_ledger_entries WHERE color = :a"), {"a": "red"})
        red_ml = result.first()[0]
        if red_ml == None: red_ml = 0
        result = connection.execute(sqlalchemy.text("SELECT SUM(change) AS green_ml FROM ml_ledger_entries WHERE color = :a"), {"a": "green"})
        green_ml = result.first()[0]
        if green_ml == None: green_ml = 0
        result = connection.execute(sqlalchemy.text("SELECT SUM(change) AS blue_ml FROM ml_ledger_entries WHERE color = :a"), {"a": "blue"})
        blue_ml = result.first()[0]
        if blue_ml == None: blue_ml = 0
        result = connection.execute(sqlalchemy.text("SELECT SUM(change) AS dark_ml FROM ml_ledger_entries WHERE color = :a"), {"a": "dark"})
        dark_ml = result.first()[0]
        if dark_ml == None: dark_ml = 0
        
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
    ml_change = [0, 0, 0, 0]
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
                    ml_change[0] += barrel.ml_per_barrel
        elif color == "green":
            if barrel.potion_type == [0, 1, 0, 0]:
                if temp_gold >= barrel.price:
                    cart.append({
                        "sku": barrel.sku,
                        "quantity": 1
                    })
                    temp_gold -= barrel.price
                    ml_change[1] += barrel.ml_per_barrel
        elif color == "blue":
            if barrel.potion_type == [0, 0, 1, 0]:
                if temp_gold >= barrel.price:
                    cart.append({
                        "sku": barrel.sku,
                        "quantity": 1
                    })
                    temp_gold -= barrel.price
                    ml_change[2] += barrel.ml_per_barrel
        else:
            if barrel.potion_type == [0, 0, 0, 1]:
                if temp_gold >= barrel.price:
                    cart.append({
                        "sku": barrel.sku,
                        "quantity": 1
                    })
                    temp_gold -= barrel.price
                    ml_change[3] += barrel.ml_per_barrel

    return cart
