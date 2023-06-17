import os
import shutil
import time
from flask import Flask, render_template, request, session, redirect, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from Assets.handlers import DatabaseAPI
from Assets.Utilities import login_required, already_logged_in, generate_random_charachters
from Backend.ingest import Ingest
from Backend.Prompt import Prompt
from threading import Thread
import concurrent.futures

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config.update(SESSION_SAME_SITE="None", SESSION_COOKIE_SECURE=True)
Session(app)

class Check:
    ingesting = False
    prompting = False
    prompter = None

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# The pages 
@app.route("/")
@already_logged_in
def index():
    """Main Index Page"""
    session.update()

    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
@already_logged_in
def login():
    """Log user in"""
    database = DatabaseAPI()

    # User reached route via GET
    if request.method == "GET":  
        return render_template("login.html")
    else:
        username =  request.form.get("username")
        password =  request.form.get("password")

        if not database.checkUser(username):
            return render_template("login.html", error="invalid username")
        
        if not database.approveUser(username, password):
            return render_template("login.html", error="wrong password")
        
        user_data = database.selectUser(username)

        session['id '] = user_data['id']
        session['name'] = user_data['name']
        session['username'] = user_data['username']
        session['email'] = user_data['email']

    return redirect("/upload")


@app.route("/register", methods=["GET", "POST"])
@already_logged_in
def register():
    "Register Page"
    if request.method == "GET":
        return render_template("register.html")
    elif request.method == "POST":
        name =  request.form.get("name")
        username =  request.form.get("username")
        email=  request.form.get("email")
        password =  request.form.get("password")

        hashpassword = generate_password_hash(password)
        
        database = DatabaseAPI()

        

        if database.checkUser(username):
            return render_template("register.html", username=True)
        
        database.insertUser({"name": name, "username": username, "email": email, "password": hashpassword})

        user_data = database.selectUser(username)

        session['id '] = user_data['id']
        session['name'] = user_data['name']
        session['username'] = user_data['username']
        session['email'] = user_data['email']

            
    return redirect("/upload")

@app.route('/check_ingesting')
def check_ingesting():
    # Perform the necessary logic to determine if the condition is met
    

    # Return the result as a JSON response
    return jsonify({'condition_met': Check.ingesting})

@app.route('/check_prompting')
def check_prompting():
    # Perform the necessary logic to determine if the condition is met
    

    # Return the result as a JSON response
    return jsonify({'condition_met': Check.prompting})

@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    # delete all temp folder
    q = request.args.get("q")
    if q:
        shutil.rmtree(os.path.join("db", q))
        shutil.rmtree(os.path.join("uploads", q))
    Check.ingesting = False
    Check.prompting = False
    Check.prompter = None
    if request.method == "GET":
        return render_template("upload.html") 
    chars = generate_random_charachters()
    files = request.files.getlist('file')
    os.makedirs(f"uploads/{chars}")
    # os.makedirs(f"db/{chars}")
    for fl in files:
        fl.save(os.path.join('uploads', str(chars), fl.filename))
    return redirect(f"/ingest?q={chars}")

@app.route("/process", methods=["GET", "POST"])
@login_required
def process():

    chars = request.args.get("q")
  
    return render_template("process.html", q=chars)

@app.route("/prepare", methods=["GET", "POST"])
@login_required
def prepare():

    
    folder = request.args.get("q")
    thread = Thread(target=execute_prompting, args=(folder,))
    thread.start()
  
    return render_template("prepare.html", q=folder)

@app.route("/ingest", methods=["GET", "POST"])
@login_required
def ingest():
    folder = request.args.get("q")
    thread = Thread(target=execute_ingestion, args=(folder,))
    thread.start()
    
 
    return redirect(f"/process?q={folder}")

def execute_ingestion(folder):
    ingest = Ingest(os.path.join("uploads", folder), os.path.join("db", folder), os.environ.get("EMBEDDINGS_MODEL_NAME"))
    ingest.Process()

    Check.ingesting = True


@app.route("/error", methods=["GET", "POST"])
@login_required
def error():
    message = request.args.get("message")
    return render_template("error.html", message=message)


@app.route("/prompt", methods=["GET", "POST"])
@login_required
def prompt():
    folder = request.args.get("q")
 
    return render_template("prompt.html") 

def execute_prompting(folder):
    Check.prompter = Prompt(folder)
    p = Check.prompter.Process()
    if p is None:
        Check.prompting = True
    else:
        print(p)

    

@app.route("/logout")
@login_required
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # delete all temp folder
    q = request.args.get("q")
    if q:
        shutil.rmtree(os.path.join("db", q))
        shutil.rmtree(os.path.join("uploads", q))

    # Redirect user to login form
    return redirect("/")

@app.route("/query")
@login_required
def query():
    q = request.args.get("q")
   
    return Check.prompter.Output(q)

# for errors
@app.errorhandler(404)
def page_not_found(e):
    return render_template("issue.html", message=e), 404