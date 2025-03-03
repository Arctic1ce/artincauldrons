create table
  public.cart_items (
    cart_id integer not null,
    item_sku text not null,
    quantity integer not null,
    line_item_id integer generated by default as identity,
    created_at timestamp with time zone not null default (now() at time zone 'utc'::text),
    line_item_total integer not null default 0,
    constraint cart_items_pkey primary key (line_item_id),
    constraint cart_items_id_key unique (line_item_id)
  ) tablespace pg_default;
