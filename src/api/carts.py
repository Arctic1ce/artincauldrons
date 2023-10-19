import re
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

    id = -1
    with db.engine.begin() as connection:
        stmt = sqlalchemy.text("INSERT INTO cart (customer) VALUES (:a)")
        result = connection.execute(stmt, {"a": new_cart.customer})
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
        for row in result: # if item is already in cart
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

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        row = result.first()

        gold = row.gold
        num_potions = 0
        cost = 0

        potion_types = []
        quantities = []
        stmt = sqlalchemy.text("SELECT * FROM cart_items WHERE cart_id = :a")
        result = connection.execute(stmt, {"a": cart_id})
        result_dict = result.mappings().all()
        for row in result_dict:
            requested_quantity = row["quantity"]
            item_sku = row["item_sku"]
            stmt = sqlalchemy.text("SELECT * FROM potions WHERE item_sku = :a")
            result = connection.execute(stmt, {"a": item_sku})
            row = result.first()

            num_potion = row.quantity
            if num_potion >= requested_quantity:
                potion_types.append(row.potion_type)
                quantities.append(num_potion*-1)
                num_potions += requested_quantity
                cost += (requested_quantity * row.item_price)
                result = connection.execute(sqlalchemy.text("UPDATE potions SET quantity = quantity-:a WHERE item_sku = :b"), {"a": requested_quantity, "b": item_sku})
                
        gold = gold + cost
        stmt = sqlalchemy.text("UPDATE global_inventory SET gold = :a")
        result = connection.execute(stmt, {"a": gold})

        stmt = sqlalchemy.text("INSERT INTO transactions (potion_type, quantity) VALUES (:a, :b)")
        result = connection.execute(stmt, {"a": potion_types, "b": quantities})

        result = connection.execute(sqlalchemy.text("SELECT * FROM transactions ORDER BY created_at DESC LIMIT 1"))
        row = result.first()
        transaction_id = row.id

        stmt = sqlalchemy.text("INSERT INTO gold_ledger_entries (transaction_id, change) VALUES (:a, :b)")
        result = connection.execute(stmt, {"a": transaction_id, "b": cost})

        for i in range(len(potion_types)):
            stmt = sqlalchemy.text("INSERT INTO potions_ledger_entries (transaction_id, potion_type, change) VALUES (:a, :b, :c)")
            result = connection.execute(stmt, {"a": transaction_id, "b": potion_types[i], "c": quantities[i]})

        

    return {"total_potions_bought": num_potions, "total_gold_paid": cost}
