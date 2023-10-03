from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth

import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)


class NewCart(BaseModel):
    customer: str


@router.post("/")
def create_cart(new_cart: NewCart):
    """ """

    with db.engine.begin() as connection:
        stmt = sqlalchemy.text("INSERT INTO cart (customer) VALUES (:a)")
        result = connection.execute(stmt, {"a": new_cart.customer})
    
    id = -1
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT cart_id FROM cart ORDER BY cart_id DESC LIMIT 1"))
        for row in result:
            id = row[0]

    return {"cart_id": id}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """

    customer = ""
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT customer FROM cart WHERE cart_id = :a"), {"a": cart_id})
        for row in result:
            customer = row[0]

    return {"cart_id": cart_id, "customer": customer}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """

    with db.engine.begin() as connection:
        stmt = sqlalchemy.text("SELECT * FROM cart_items WHERE (cart_id = :a AND item_sku = :b)")
        result = connection.execute(stmt, {"a": cart_id, "b": item_sku})

        exists = False
        for row in result: # if item is not already in cart
            exists = True
            with db.engine.begin() as connection:
                stmt = sqlalchemy.text("UPDATE cart_items SET quantity = :a")
                result = connection.execute(stmt, {"a": cart_item.quantity})
            break
        if not exists:
            with db.engine.begin() as connection:
                stmt = sqlalchemy.text("INSERT INTO cart_items (cart_id, item_sku, quantity) VALUES (:a, :b, :c)")
                result = connection.execute(stmt, {"a": cart_id, "b": item_sku, "c": cart_item.quantity})

    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """

    red_potions = 0
    green_potions = 0
    blue_potions = 0
    gold = 0
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))

        row = result.first()
        red_potions = row.num_red_potions
        green_potions = row.num_green_potions
        blue_potions = row.num_blue_potions
        gold = row.gold
        
    potions = [0, 0, 0]
    with db.engine.begin() as connection:
        stmt = sqlalchemy.text("SELECT * FROM cart_items WHERE cart_id = :a")
        result = connection.execute(stmt, {"a": cart_id})
        for row in result:
            if row[1] == "RED_POTION_0":
                potions[0] = row[2]
            elif row[1] == "GREEN_POTION_0":
                potions[1] = row[2]
            elif row[2] == "BLUE_POTION_0":
                potions[2] = row[2]

    if potions[0] > red_potions:
        potions[0] = red_potions
    if potions[1] > green_potions:
        potions[1] = green_potions
    if potions[2] > blue_potions:
        potions[2] = blue_potions

    red_potions = red_potions - potions[0]
    green_potions = green_potions - potions[1]
    blue_potions = blue_potions - potions[2]

    num_potions = red_potions + green_potions + blue_potions

    cost = num_potions * 50
    gold = gold + cost

    with db.engine.begin() as connection:
        stmt = sqlalchemy.text("UPDATE global_inventory SET num_red_potions = :a, num_green_potions = :b, num_blue_potions = :c, gold = :d")
        result = connection.execute(stmt, {"a": red_potions, "b": green_potions, "c": blue_potions, "d": gold})

    return {"total_potions_bought": num_potions, "total_gold_paid": cost}
