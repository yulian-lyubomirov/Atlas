-- Postgres init for: profile, asset, savings_account, deposit, asset_transaction, asset_holding

begin;

-- ---------- Enums ----------
do $$
begin
	if not exists (select 1 from pg_type where typname = 'asset_type') then
		create type asset_type as enum ('stock', 'crypto', 'etf', 'bond', 'other');
	end if;
end
$$;

-- ---------- Core ----------
create table if not exists profile (
	id bigserial primary key,
	name text not null,
	creation_date timestamptz not null default now()
);

create table if not exists asset (
	id bigserial primary key,
	name text not null,
	type asset_type not null,
	creation_date timestamptz not null default now()
);

-- ---------- Savings ----------
create table if not exists savings_account (
	id bigserial primary key,
	user_id bigint not null references profile(id) on delete cascade,
	currency char(3) not null,
	annual_interest_rate numeric(10, 6) not null check (annual_interest_rate >= 0),
	creation_date timestamptz not null default now()
);

create index if not exists ix_savings_account_user
	on savings_account(user_id);

create table if not exists deposit (
	id bigserial primary key,
	user_id bigint not null references profile(id) on delete cascade,
	savings_account_id bigint not null references savings_account(id) on delete cascade,
	quantity numeric(24, 8) not null,
	date timestamptz not null
);

create index if not exists ix_deposit_account_date
	on deposit(savings_account_id, date);

create index if not exists ix_deposit_user_date
	on deposit(user_id, date);

-- ---------- Portfolio ----------
-- NOTE: avoid naming a table "transaction" (keyword-ish); use asset_transaction
create table if not exists asset_transaction (
	id bigserial primary key,
	user_id bigint not null references profile(id) on delete cascade,
	asset_id bigint not null references asset(id) on delete restrict,
	quantity numeric(24, 8) not null, -- signed: +buy, -sell
	price numeric(24, 8) not null,
	date timestamptz not null
);

create index if not exists ix_asset_tx_user_date
	on asset_transaction(user_id, date);

create index if not exists ix_asset_tx_user_asset_date
	on asset_transaction(user_id, asset_id, date);

-- Lightweight holdings cache (materialized summary)
create table if not exists asset_holding (
	id bigserial primary key,
	user_id bigint not null references profile(id) on delete cascade,
	asset_id bigint not null references asset(id) on delete restrict,
	quantity numeric(24, 8) not null default 0,
	last_activity_date timestamptz not null,
	constraint uq_holding_user_asset unique (user_id, asset_id)
);

create index if not exists ix_asset_holding_user
	on asset_holding(user_id);

create index if not exists ix_asset_holding_user_asset
	on asset_holding(user_id, asset_id);

commit;
