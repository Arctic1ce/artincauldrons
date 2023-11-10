from enum import Enum
import re
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth

import sqlalchemy
from src import database as db
import math

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    metadata_obj = sqlalchemy.MetaData()
    cart = sqlalchemy.Table("cart", metadata_obj, autoload_with=db.engine)
    cart_items = sqlalchemy.Table("cart_items", metadata_obj, autoload_with=db.engine)
    potions = sqlalchemy.Table("potions", metadata_obj, autoload_with=db.engine)

    if sort_col is search_sort_options.customer_name:
        order_by = cart.c.customer
    elif sort_col is search_sort_options.item_sku:
        order_by = cart_items.c.item_sku
    elif sort_col is search_sort_options.line_item_total:
        order_by = cart_items.c.line_item_total
    elif sort_col is search_sort_options.timestamp:
        order_by = cart_items.c.created_at
    else:
        assert False
    
    if sort_order is search_sort_order.asc:
        order_by = order_by.asc()
    elif sort_order is search_sort_order.desc:
        order_by = order_by.desc()
    else:
        assert False

    if search_page != "":
        offset = int(search_page) * 5
        page = int(search_page)
    else:
        offset = 0
        page = 0

    j = sqlalchemy.join(cart_items, cart, cart_items.c.cart_id == cart.c.cart_id).join(potions, cart_items.c.item_sku == potions.c.item_sku)
    stmt = (
        sqlalchemy.select(cart_items, cart, potions).select_from(j)
        .order_by(order_by)
    )

    if customer_name != "":
        stmt = stmt.where(cart.c.customer.ilike(f"%{customer_name}%"))
    if potion_sku != "":
        stmt = stmt.where(cart_items.c.item_sku.ilike(f"%{potion_sku}%"))

    with db.engine.connect() as connection:
        result = connection.execute(stmt)
        num_items = result.rowcount
        result = connection.execute(stmt.limit(5).offset(offset))
        json = []
        for row in result:
            print(row)
            json.append(
                {
                    "line_item_id": row.line_item_id,
                    "item_sku": row.item_sku,
                    "customer_name": row.customer,
                    "line_item_total": row.line_item_total,
                    "timestamp": row.created_at,
                }
            )

    if page > 0:
        previous = str(page-1)
    else:
        previous = ""
    if page < (math.ceil(num_items/5) - 1):
        next = str(page+1)
    else:
        next = ""

    return {
        "previous": previous,
        "next": next,
        "results": json,
    }


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

    try:
        with db.engine.begin() as connection:
            result = connection.execute(sqlalchemy.text("SELECT SUM(change) AS gold FROM gold_ledger_entries"))
            gold = result.first()[0]

            num_potions = 0
            cost = 0

            potion_types = []
            quantities = []
            skus = []
            costs = []
            stmt = sqlalchemy.text("SELECT * FROM cart_items WHERE cart_id = :a")
            result = connection.execute(stmt, {"a": cart_id})
            result_dict = result.mappings().all()
            for row in result_dict:
                requested_quantity = row["quantity"]
                item_sku = row["item_sku"]
                stmt = sqlalchemy.text("SELECT * FROM potions WHERE item_sku = :a")
                result = connection.execute(stmt, {"a": item_sku})
                row = result.first()
                potion_type = row.potion_type

                result = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM potions_ledger_entries WHERE potion_type = :a"), {"a": potion_type})
                quantity = result.first()[0]
                if quantity >= requested_quantity:
                    potion_types.append(potion_type)
                    quantities.append(requested_quantity*-1)
                    skus.append(item_sku)
                    costs.append(requested_quantity * row.item_price)
                    num_potions += requested_quantity
                    cost += (requested_quantity * row.item_price)

            stmt = sqlalchemy.text("INSERT INTO transactions (potion_type, quantity, gold) VALUES (:a, :b, :c)")
            result = connection.execute(stmt, {"a": potion_types, "b": quantities, "c": cost})

            result = connection.execute(sqlalchemy.text("SELECT * FROM transactions ORDER BY created_at DESC LIMIT 1"))
            row = result.first()
            transaction_id = row.id

            stmt = sqlalchemy.text("INSERT INTO gold_ledger_entries (transaction_id, change) VALUES (:a, :b)")
            result = connection.execute(stmt, {"a": transaction_id, "b": cost})

            for i in range(len(potion_types)):
                stmt = sqlalchemy.text("INSERT INTO potions_ledger_entries (transaction_id, potion_type, change) VALUES (:a, :b, :c)")
                result = connection.execute(stmt, {"a": transaction_id, "b": potion_types[i], "c": quantities[i]})
                stmt = sqlalchemy.text("UPDATE cart_items SET line_item_total = :a WHERE cart_id = :b AND item_sku = :c")
                result = connection.execute(stmt, {"a": costs[i], "b": cart_id, "c": skus[i]})
    except Exception as ex:
        raise Exception(ex)
        

    return {"total_potions_bought": num_potions, "total_gold_paid": cost}
