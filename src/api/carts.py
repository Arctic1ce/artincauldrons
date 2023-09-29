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
    
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT cart_id FROM cart ORDER BY cart_id DESC LIMIT 1"))
        for row in result:
            print(row[0])

    return {"cart_id": row[0]}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """

    return {}


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
    gold = 0
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        for row in result:
            red_potions = row[0]
            gold = row[2]

    with db.engine.begin() as connection:
        stmt = sqlalchemy.text("SELECT quantity FROM cart_items WHERE (cart_id = :a AND item_sku = 'RED_POTION_0')")
        result = connection.execute(stmt, {"a": cart_id})
        for row in result:
            print(row[0])
    quantity = row[0]

    if quantity > red_potions:
        quantity = red_potions
    red_potions = red_potions - quantity

    cost = quantity * 50
    gold = gold + cost

    with db.engine.begin() as connection:
        stmt = sqlalchemy.text("UPDATE global_inventory SET num_red_potions = :a, gold = :b")
        result = connection.execute(stmt, {"a": red_potions, "b": gold})

    return {"total_potions_bought": quantity, "total_gold_paid": cost}
