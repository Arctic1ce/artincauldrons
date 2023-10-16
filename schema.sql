create table
  public.global_inventory (
    num_red_ml integer not null,
    gold integer not null default 100,
    num_green_ml integer not null default 0,
    num_blue_ml integer not null default 0,
    id integer not null default 1,
    num_dark_ml integer not null default 0,
    constraint global_inventory_pkey primary key (id)
  ) tablespace pg_default;

create table
  public.potions (
    id bigint generated by default as identity,
    item_sku text not null,
    item_price integer not null,
    quantity integer not null,
    item_name text not null,
    potion_type integer[] not null,
    constraint potions_pkey primary key (id)
  ) tablespace pg_default;

create table
  public.cart (
    cart_id integer generated by default as identity,
    customer text not null,
    constraint cart_pkey primary key (cart_id)
  ) tablespace pg_default;

create table
  public.cart_items (
    cart_id integer not null,
    item_sku text not null,
    quantity integer not null,
    constraint cart_items_pkey primary key (cart_id, item_sku)
  ) tablespace pg_default;