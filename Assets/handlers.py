from Assets.database import *
from Assets.Utilities import normalise_data
from werkzeug.security import check_password_hash, generate_password_hash

class DatabaseAPI:
    def __init__(self) -> None:
        self.database = Database("Assets/database.db")
        self.database.connect()

       
    def getAllUsers(self):
        users = self.database.select_data("users", "*")
        return users
    def insertUser(self, data: dict):
        self.database.insert_data("users", data)
    
    def checkUser(self, username: str)->bool:
      
        if username in normalise_data(self.database.select_data("users", ["username"])):
            return True
        return False
    
    def approveUser(self, username:str, password: str):

        if check_password_hash(normalise_data(self.database.select_specific_data("users", ["password"], "username", username))[0], password):
            return True
        return False
    
    def selectUser(self, username: str):
        columns = ["id", "name", "username", "email"]
        data = normalise_data(self.database.select_specific_data("users", ["id", "name", "username", "email"], "username", username))[0]
        
        return_data = dict()
       

        for index, column in enumerate(columns):
            return_data[column] = data[index]
        return return_data

