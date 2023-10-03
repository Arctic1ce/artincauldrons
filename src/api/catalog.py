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
    red_potions = 0
    green_potions = 0
    blue_potions = 0
    potions = []
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))

        row = result.first()
        potions.append(row.num_red_potions)
        potions.append(row.num_green_potions)
        potions.append(row.num_blue_potions)

    result = []
    for i in range(len(potions)):
        if potions[i] > 0:
            if i == 0:
                result.append({
                                "sku": "RED_POTION_0",
                                "name": "red potion",
                                "quantity": potions[i],
                                "price": 50,
                                "potion_type": [100, 0, 0 ,0],
                            })
            elif i == 1:
                result.append({
                                "sku": "GREEN_POTION_0",
                                "name": "green potion",
                                "quantity": potions[i],
                                "price": 50,
                                "potion_type": [0, 100, 0 ,0],
                            })
            else:
                result.append({
                                "sku": "BLUE_POTION_0",
                                "name": "blue potion",
                                "quantity": potions[i],
                                "price": 60,
                                "potion_type": [0, 0, 100 ,0],
                            })

    return result
