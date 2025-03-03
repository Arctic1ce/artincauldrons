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
