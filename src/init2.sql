-- Entry type enum
CREATE TYPE entry_type_enum AS ENUM ('deposit', 'withdrawal');

-- Reference tables
CREATE TABLE asset_type (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE currency (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    creation_date TIMESTAMP NOT NULL DEFAULT now()
);

-- Assets
CREATE TABLE asset (
    isin TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    currency_id INT NOT NULL REFERENCES currency(id),
    asset_type_id INT NOT NULL REFERENCES asset_type(id),
    name TEXT NOT NULL,
    creation_date TIMESTAMP NOT NULL DEFAULT now()
);

-- Asset data
CREATE TABLE asset_data (
    asset_isin TEXT NOT NULL REFERENCES asset(isin),
    date DATE NOT NULL,
    mid_close NUMERIC(18,8),
    high NUMERIC(18,8),
    low NUMERIC(18,8),
    open NUMERIC(18,8),
    volume INTEGER,
    PRIMARY KEY (asset_isin, date)
);

-- Transactions
CREATE TABLE asset_transaction (
    user_id INT NOT NULL REFERENCES users(id),
    asset_isin TEXT NOT NULL REFERENCES asset(isin),
    quantity NUMERIC(18,8) NOT NULL,
    price NUMERIC(18,8) NOT NULL,
    date TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, asset_isin, date)
);

-- Savings account
CREATE TABLE savings_account (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id),
    currency_id INT NOT NULL REFERENCES currency(id),
    creation_date TIMESTAMP NOT NULL DEFAULT now(),
    annual_interest_rate NUMERIC(5,4) NOT NULL
);

-- Account entries
CREATE TABLE account_entry (
    savings_account_id INT NOT NULL REFERENCES savings_account(id),
    entry_type entry_type_enum NOT NULL,
    quantity NUMERIC(18,8) NOT NULL,
    date TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (savings_account_id, date)
);

-- Materialized view
CREATE MATERIALIZED VIEW asset_holding AS
SELECT
    t.user_id,
    t.asset_isin,
    MIN(t.date) AS creation_date,
    CASE
        WHEN SUM(t.quantity) > 0 THEN 'open'
        ELSE 'closed'
    END AS status,
    SUM(t.quantity * t.price) / NULLIF(SUM(t.quantity), 0) AS avg_price,
    MAX(t.date) AS last_activity_date
FROM asset_transaction t
GROUP BY t.user_id, t.asset_isin;

REFRESH MATERIALIZED VIEW asset_holding;

-- Indexes
CREATE INDEX idx_transaction_user ON asset_transaction (user_id);
CREATE INDEX idx_transaction_asset ON asset_transaction (asset_isin);
CREATE INDEX idx_asset_data_asset_date ON asset_data (asset_isin, date);
CREATE INDEX idx_account_entry_account ON account_entry (savings_account_id);
