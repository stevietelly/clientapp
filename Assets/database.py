import sqlite3
from typing import Tuple, Union

class Database:
    def __init__(self, db_file):
        self.db_file = db_file
        self.connection = None

    def connect(self)->Tuple[bool, str]:
        try:
            self.connection = sqlite3.connect(self.db_file)
            return True, "connected succesfully"
        except sqlite3.Error as e:
            return False, e

    def close(self):
        if self.connection:
            self.connection.close()
            return True, "disconnected succesfully"
        return True, "already disconnected"

    def execute_query(self, query)->Tuple[bool, str]:
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            self.connection.commit()
            return True, "Query executed successfully!"
        except sqlite3.Error as e:
            return False, e

    def create_table(self, table_name, columns)->Tuple[bool, str]:
        column_str = ", ".join(columns)
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({column_str})"
        return self.execute_query(query)

    def insert_data(self, table_name, data)->Tuple[bool, str]:
        column_str = ", ".join(data.keys())
        value_str = ", ".join([f"'{value}'" for value in data.values()])
        query = f"INSERT INTO {table_name} ({column_str}) VALUES ({value_str})"
        return self.execute_query(query)

    def select_data(self, table_name: str, columns: Union[None, list]=None):
        if columns:
            column_str = ", ".join(columns)
        else:
            column_str = "*"
        query = f"SELECT {column_str} FROM {table_name}"
        cursor = self.connection.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        return rows
    def select_specific_data(self, table_name: str, columns: Union[None, list], specific_column: str, specific_data: str):
        if columns:
            column_str = ", ".join(columns)
        else:
            column_str = "*"
        query = f"SELECT {column_str} FROM {table_name} WHERE {specific_column}=\'{specific_data}\'"


        cursor = self.connection.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        return rows



