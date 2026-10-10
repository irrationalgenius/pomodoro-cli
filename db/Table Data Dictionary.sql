
create table data_dictionary
(
    table_name      TEXT not null,
    column_name     TEXT not null,
    description     TEXT,
    possible_values TEXT,
    primary key (table_name, column_name)
);

