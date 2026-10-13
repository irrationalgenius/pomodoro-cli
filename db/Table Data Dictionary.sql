
DROP TABLE IF EXISTS data_dictionary CASCADE;
CREATE TABLE data_dictionary (
    table_name      TEXT NOT NULL,
    column_name     TEXT NOT NULL,
    description     TEXT,
    possible_values TEXT,
    PRIMARY KEY (table_name, column_name)
);

