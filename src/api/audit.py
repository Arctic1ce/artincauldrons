from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math

import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/inventory")
def get_inventory():
    """ """
    potions = 0
    ml = 0
    gold = 0
    with db.engine.begin() as connection:
        
        # DELETE these queries
        # result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        # row = result.first()
        # ml = row.num_red_ml + row.num_green_ml + row.num_blue_ml + row.num_dark_ml
        # gold = row.gold

        # result = connection.execute(sqlalchemy.text("SELECT * FROM potions"))
        # result_dict = result.mappings().all()
        # for row in result_dict:
        #     potions += row["quantity"]

        result = connection.execute(sqlalchemy.text("SELECT SUM(change) AS gold FROM gold_ledger_entries"))
        gold = result.first()[0]

        result = connection.execute(sqlalchemy.text("SELECT SUM(change) AS potions FROM potions_ledger_entries"))
        potions = result.first()[0]

        result = connection.execute(sqlalchemy.text("SELECT SUM(change) AS ml FROM ml_ledger_entries"))
        ml = result.first()[0]
    
    return {"number_of_potions": potions, "ml_in_barrels": ml, "gold": gold}

class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool

# Gets called once a day
@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """
    print(audit_explanation)

    return "OK"
