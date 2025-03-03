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
    line_item_id integer generated by default as identity,
    created_at timestamp with time zone not null default (now() at time zone 'utc'::text),
    constraint cart_items_pkey primary key (line_item_id),
    constraint cart_items_id_key unique (line_item_id)
  ) tablespace pg_default;

create table
  public.gold_ledger_entries (
    id integer generated by default as identity,
    transaction_id integer not null,
    change integer not null default 0,
    constraint transactions_pkey primary key (id)
  ) tablespace pg_default;

create table
  public.ml_ledger_entries (
    id bigint generated by default as identity,
    transaction_id integer not null,
    color text not null,
    change integer not null,
    constraint ml_ledger_entries_pkey primary key (id)
  ) tablespace pg_default;

create table
  public.potions (
    id bigint generated by default as identity,
    item_sku text not null,
    item_price integer not null,
    item_name text not null,
    potion_type integer[] not null,
    constraint potions_pkey primary key (id)
  ) tablespace pg_default;

create table
  public.potions_ledger_entries (
    id integer generated by default as identity,
    transaction_id integer not null,
    potion_type integer[] not null,
    change integer not null,
    constraint potions_ledger_entries_pkey primary key (id)
  ) tablespace pg_default;

create table
  public.transactions (
    id integer generated by default as identity,
    created_at timestamp with time zone not null default now(),
    potion_type integer[] null,
    quantity integer[] null,
    red_ml integer null,
    green_ml integer null,
    blue_ml integer null,
    dark_ml integer null,
    gold integer null,
    constraint transactions_pkey1 primary key (id)
  ) tablespace pg_default;