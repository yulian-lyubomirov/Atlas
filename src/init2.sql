-- Entry type enum
CREATE TYPE entry_type_enum AS ENUM ('deposit', 'withdrawal');

CREATE TABLE asset_type (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE currency (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE profile (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    creation_date TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE asset (
    id SERIAL PRIMARY KEY,
    asset_type_id INT NOT NULL REFERENCES asset_type(id),
    name TEXT NOT NULL,
    creation_date TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE data (
    id SERIAL PRIMARY KEY,
    asset_id INT NOT NULL REFERENCES asset(id),
    date DATE NOT NULL,
    mid_close NUMERIC(18,8),
    bid NUMERIC(18,8),
    ask NUMERIC(18,8),
    UNIQUE(asset_id, date)
);

CREATE TABLE transaction (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES profile(id),
    asset_id INT NOT NULL REFERENCES asset(id),
    quantity NUMERIC(18,8) NOT NULL,
    price NUMERIC(18,8) NOT NULL,
    date TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE savings_account (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES profile(id),
    currency_id INT NOT NULL REFERENCES currency(id),
    creation_date TIMESTAMP NOT NULL DEFAULT now(),
    annual_interest_rate NUMERIC(5,4) NOT NULL
);

CREATE TABLE account_entry (
    id SERIAL PRIMARY KEY,
    savings_account_id INT NOT NULL REFERENCES savings_account(id),
    entry_type entry_type_enum NOT NULL,
    quantity NUMERIC(18,8) NOT NULL,
    date TIMESTAMP NOT NULL DEFAULT now()
);

CREATE MATERIALIZED VIEW asset_holding AS
SELECT
    t.user_id,
    t.asset_id,
    MIN(t.date) AS creation_date,
    CASE
        WHEN SUM(t.quantity) > 0 THEN 'open'
        ELSE 'closed'
    END AS status,
    SUM(t.quantity * t.price) / NULLIF(SUM(t.quantity), 0) AS avg_price,
    MAX(t.date) AS last_activity_date
FROM transaction t
GROUP BY t.user_id, t.asset_id;

REFRESH MATERIALIZED VIEW asset_holding;

CREATE INDEX idx_transaction_user ON transaction(user_id);
CREATE INDEX idx_transaction_asset ON transaction(asset_id);
CREATE INDEX idx_data_asset_date ON data(asset_id, date);
CREATE INDEX idx_account_entry_account ON account_entry(savings_account_id);
