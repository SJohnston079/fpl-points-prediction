import duckdb
import pathlib


ddl = pathlib.Path('src/data-ingestion/raw-vault.sql').read_text()


with duckdb.connect('data/ingested/fpl_pipeline.duckdb') as con:
    #con.sql(ddl)

    print(con.sql('SHOW TABLES'))