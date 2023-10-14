from re import L
from fastapi import APIRouter

import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    # Can return a max of 20 items.
    results = []
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM potions"))
        result_dict = result.mappings().all()
        for row in result_dict:
            if row["quantity"] > 0:
                results.append({
                    "sku": row["item_sku"],
                    "name": row["item_name"],
                    "quantity": row["quantity"],
                    "price": row["item_price"],
                    "potion_type": row["potion_type"],
                })

    return results
