from typing import List
from functools import wraps
from flask import redirect, session
import uuid

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("username") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function

def already_logged_in(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("username") is None:
            return redirect("/upload")
        return f(*args, **kwargs)
    return decorated_function

def normalise_data(data: List[set]):
    retr_data = []
    for item in data:
        if len(item) == 1:
            retr_data.append(*item)
        else:
            retr_data.append(list(item))
    return retr_data

def generate_random_charachters():
    return uuid.uuid4()
