import mysql.connector
from mysql.connector import Error
import pandas as pd
import os
from pathlib import Path


class Utils():

    def __init__(self) -> None:
        pass
    
    @property
    def sample_count(self) ->int:
        return 5
    
    def pathinfo(self):
        print(f'current dir - {os.getcwd()}')
        # import sys
        # print(f'sys    path - {sys.path}')
        print(f'parent dir - {os.pardir}')
        print(f'parent dir abs path - {os.path.abspath(os.pardir)}')
        print(f'curr dir - {os.path.abspath(os.getcwd())}')
        print(f'joined path - {os.path.join(os.getcwd(), os.pardir)}')
        print(f'curr dir - {os.getcwd()}')
        print(f'curr dir abs path - {os.path.abspath(os.getcwd())}')
        print(f'FILE abs path  - {(os.path.abspath(__file__))}')
        print(f'FILE dir path  - {Path(os.path.dirname(__file__)).parent}')
        print(f'FILE real path  - {(os.path.realpath(__file__))}')

        print(f'joined path - {os.path.join(os.getcwd(), os.pardir)}')
        print(f'joined abs path - {os.path.abspath(os.path.join(os.getcwd(), os.pardir))}')
        

    def get_store_products_from_file(self, filename, storeid=None, category: list=None) -> list:
        input_file=filename
        
        df = pd.read_csv(os.path.join(Path(os.path.dirname(__file__)).parent, 'data', input_file), header=0)
        
        if storeid and storeid!=0:
            df=df[df['store']==storeid]
        
        if category:
            df=df[df['department'].isin(category)]
            
        d={'Y': 1, 'N': 0}
        df['isinpromotion']=df['isinpromotion'].map(d)
        
        df = df.sort_values(by=['inventory','isinpromotion'], ascending=[False, True])
        if df['product'].count()>0 :            
            pdt = df['product'].drop_duplicates().head(self.sample_count)
            return pdt
            # pdt_str = ', '.join(pdt)
            # return pdt_str
        else:
            return []


    def get_store_products(self, storeid=None, category: list[str]=None) -> list:
        connection = None
        try:
            # TODO: Implement MySQLConnectionPool connection pooling & call connection=pool.get_connection() instead of mysql.connector.connect()
            connection = mysql.connector.connect(
                host=os.getenv("MYSQL_HOST"),
                user=os.getenv("MYSQL_USER"),
                password=os.getenv("MYSQL_PASSWORD"),
                database=os.getenv("MYSQL_DB"),
                port=os.getenv("MYSQL_PORT")
            )

            if connection.is_connected():
                print("Connected to MySQL database")
                
                # create cursor object
                with connection.cursor(dictionary=True) as cursor:
                    query = "SELECT product FROM store_items"

                    # dynamic filter structures
                    conditions = []
                    query_params = []

                    if storeid and storeid!=0:
                        conditions.append("store=%s")
                        query_params.append(storeid)
                    if category:
                        conditions.append("department IN (%s)" % ','.join(['%s'] * len(category)))
                        query_params.extend(category)

                    if conditions:
                        query += " WHERE " + " AND ".join(conditions)
                    
                    # promote isinpromotion items
                    query += " ORDER BY isinpromotion DESC LIMIT %s"
                    query_params.append(self.sample_count)

                    print(f"Executing query: {query} with params: {query_params}")

                    cursor.execute(query, query_params)
                    result = cursor.fetchall()
                    print(f"Query result: {result}")
                    return result
            else:
                print("Failed to connect to MySQL database")
                return []
        except Error as e:
            print(f"Error: {e}")
            return []
        finally:
            if connection and connection.is_connected():
                connection.close()


if __name__ == "__main__":
    ## validate get_store_products method
    val = Utils().get_store_products(21, ['produce','meat'])
    print(val)
    val2 = Utils().get_store_products(202)
    print(val2)
    ##