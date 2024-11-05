CREATE TABLE users(
    id INTEGER UNIQUE generated always as IDENTITY,
    userid BIGINT PRIMARY KEY,
    role SMALLINT
);

CREATE TABLE storeditems(
    id INTEGER UNIQUE generated always as IDENTITY,
    articleNumber VARCHAR PRIMARY KEY,
    category VARCHAR,
    subcategory VARCHAR,
    name VARCHAR,
    quantity BIGINT,
    photo VARCHAR);

CREATE TABLE transactions(
    id INTEGER PRIMARY KEY generated always as IDENTITY,
    item_id INTEGER REFERENCES storeditems(id) ON DELETE CASCADE,
    transaction_type VARCHAR(10) CHECK (transaction_type IN ('add', 'sell')),
    quantity BIGINT,
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    userid BIGINT REFERENCES users(userid) ON DELETE SET NULL
);
