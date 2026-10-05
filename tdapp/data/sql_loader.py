import pandas as pd
import os
from dotenv import load_dotenv
import urllib
load_dotenv(override=True)
from sqlalchemy import create_engine, types

DB_USER=os.getenv("MYSQL_USER")
DB_PASSWORD=os.getenv("MYSQL_PASSWORD")
DB_HOST=os.getenv("MYSQL_HOST")
DB_PORT=os.getenv("MYSQL_PORT")
DB_NAME=os.getenv("MYSQL_DB")
TABLE_NAME = "store_items"
CSV_FILE = os.path.join(os.path.dirname(__file__), "meijer_products.csv")
# URL encode the password for safe usage in the connection string
SAFE_PASSWORD = urllib.parse.quote_plus(DB_PASSWORD)
print (f"sqlalchemy engine URL: mysql+pymysql://{DB_USER}:{SAFE_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

try:
    print("Reading csv data...")
    df = pd.read_csv(CSV_FILE)
    # cleanup column names in case of accidental spaces, uppercase letters
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    print("CSV data read successfully.")

    engine = create_engine(f"mysql+pymysql://{DB_USER}:{SAFE_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    # schema mapping
    # store,product,department,inventory,price,isinpromotion
    # 21,mango,produce,20,2.99,Y
    dtype_mapping = {
        "store": types.Integer,
        "product": types.VARCHAR(100),
        "department": types.VARCHAR(100),
        "inventory": types.Integer,
        "price": types.Numeric(precision=10, scale=2),
        "isinpromotion": types.VARCHAR(1)
    }

    print(f"Creating table '{TABLE_NAME}' and uploading data...")
    df.to_sql(
        name=TABLE_NAME, 
        con=engine, 
        if_exists='replace', 
        index=False, 
        dtype=dtype_mapping
    )
    print(f"Data uploaded successfully to table '{TABLE_NAME}' with {len(df)} records.")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    if 'engine' in locals():
        engine.dispose()