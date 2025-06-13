CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY,
    date TIMESTAMP,
    transaction_date TIMESTAMP,
    amount NUMERIC,
    type TEXT,
    merchant TEXT,
    account TEXT,
    card TEXT,
    reference TEXT,
    full_description TEXT,
    category TEXT
);