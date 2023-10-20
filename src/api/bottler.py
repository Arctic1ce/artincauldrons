from re import M
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
        potion_types = []
        quantities = []

        for potion in potions_delivered:
            potion_types.append(potion.potion_type)
            quantities.append(potion.quantity)
            red_ml += (potion.potion_type[0] * potion.quantity)
            green_ml += (potion.potion_type[1] * potion.quantity)
            blue_ml += (potion.potion_type[2] * potion.quantity)
            dark_ml += (potion.potion_type[3] * potion.quantity)

        red_ml *= -1
        green_ml *= -1
        blue_ml *= -1
        dark_ml *= -1
        stmt = sqlalchemy.text("INSERT INTO transactions (potion_type, quantity, red_ml, green_ml, blue_ml, dark_ml) VALUES (:a, :b, :c, :d, :e, :f)")
        result = connection.execute(stmt, {"a": potion_types, "b": quantities, "c": red_ml, "d": green_ml, "e": blue_ml, "f": dark_ml})

        result = connection.execute(sqlalchemy.text("SELECT * FROM transactions ORDER BY created_at DESC LIMIT 1"))
        row = result.first()
        transaction_id = row.id

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

        for i in range(len(potion_types)):
            stmt = sqlalchemy.text("INSERT INTO potions_ledger_entries (transaction_id, potion_type, change) VALUES (:a, :b, :c)")
            result = connection.execute(stmt, {"a": transaction_id, "b": potion_types[i], "c": quantities[i]})

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

        mls = [red_ml, green_ml, blue_ml, dark_ml]
        results = []

        result = connection.execute(sqlalchemy.text("SELECT potion_type, SUM(change) AS quantity FROM potions_ledger_entries GROUP BY potion_type ORDER BY quantity ASC"))
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
