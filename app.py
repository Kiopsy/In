import os
from datetime import date, timedelta, datetime
from flask import Flask, flash, redirect, render_template, request, session
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import sciToNum, login_required, checkDate
import sqlite3
import http.client
import json

app = Flask(__name__)

# Clears cache

@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

app.config.update(
    TESTING=True,
    SECRET_KEY=b'pk_aafb84848ef145/#2sa'
)

CLIENT_ID = "F96Uu0m1gIR85MYFWEu25yl2ul3Tjjeo"
CLIENT_SECRET = "5qQ7qVnZRRFTNM99"
REDIRECT_URI = "http://127.0.0.1:5000/dexcom"

access_token = ""
authorization_code = ""

update = ""

# Route Structure:
#       
#       Login
#       Register
# 
#       1. Account
#            a. changepass
#            b. accountdetails
#        2. Inventory
#            a. Update
#            b. Insert

@app.route("/inventory")
@login_required
def inventory():
    # Connects to database
    connection = sqlite3.connect("database.db") 
  
    # SQL Cursor
    cursor = connection.cursor()

    # Selects the account data for current user
    sql_command = "SELECT * FROM inventory WHERE id=?"
    cursor.execute(sql_command, [session["user_id"]])

    rows = cursor.fetchall()
    connection.close()

    # Renders the account page with passed in user account data
    return render_template("inventory.html", details=rows[0])

@app.route("/update", methods=["GET", "POST"])
@login_required
def update():
    # Query the existing to change the number only

    # Connect to database & get cursor
    connection = sqlite3.connect("database.db") 
    cursor = connection.cursor()

    # Selects the account data for current user
    sql_command = "SELECT * FROM inventory WHERE id=?"
    cursor.execute(sql_command, [session["user_id"]])

    # Updates the account details on the current user's account
    sql_command = "UPDATE users SET fullname=?, label=?, description=? WHERE id=?"
    cursor.execute(sql_command, [request.form.get("fullname"), request.form.get("label"), request.form.get("description"), session["user_id"]])


    rows = cursor.fetchall()
    connection.close()

    return render_template("update.html")

@app.route("/insert", methods=["GET", "POST"])
@login_required
def insert():

    if request.method == "POST":
        # Ensures the user inputted all values within the form (full name, label, and description)
        if not request.form.get("fullname") or not request.form.get("label") or not request.form.get("description") :
            flash("Must input all three values!")
            return render_template("accountdetails.html", labels=labels)
            
        # Connects to database & cursor
        connection = sqlite3.connect("database.db") 
        cursor = connection.cursor()

        # Insert an inventory entry
        sql_command = "INSERT INTO inverntory VALUES (?, ?, ?)"
        cursor.execute(sql_command, )

        # Commits SQL changes
        connection.commit()
        connection.close()

        return render_template("inventory.html")

    # User reached route via GET (as by clicking a link or via redirect)
    else: 
        return render_template("insert.html")

@app.route("/account",  methods=["GET", "POST"])
@login_required
def account():
    # Connects to database
    connection = sqlite3.connect("database.db") 
  
    # SQL Cursor
    cursor = connection.cursor()

    # Selects the account data for current user
    sql_command = "SELECT * FROM users WHERE id=?"
    cursor.execute(sql_command, [session["user_id"]])
    rows = cursor.fetchall()
    connection.close()

    # Renders the account page with passed in user account data
    return render_template("account.html", details=rows[0])

@app.route("/accountdetails",  methods=["GET", "POST"])
@login_required
def account_details():
    # The four options for labels a user can select to display on their account
    labels = ["Type-1 Diabetic", "Caregiver", "Clinical Usage", "Other"]

    if request.method == "POST":

        # Ensures the user inputted all values within the form (full name, label, and description)
        if not request.form.get("fullname") or not request.form.get("label") or not request.form.get("description") :
            flash("Must input all three values!")
            return render_template("accountdetails.html", labels=labels)

        # Ensures the submitted label is one of the four options given
        if not request.form.get("label") in labels:
            flash("Must choose a label from the presented options!")
            return render_template("accountdetails.html", labels=labels)

        # Connects to database
        connection = sqlite3.connect("database.db") 
  
        # SQL Cursor
        cursor = connection.cursor()

        # Updates the account details on the current user's account
        sql_command = "UPDATE users SET fullname=?, label=?, description=? WHERE id=?"
        cursor.execute(sql_command, [request.form.get("fullname"), request.form.get("label"), request.form.get("description"), session["user_id"]])

        # Pushes changes to database
        connection.commit()

        # Selects account data from current user
        sql_command = "SELECT * FROM users WHERE id=?"
        cursor.execute(sql_command, [session["user_id"]])
        rows = cursor.fetchall()

        connection.close()

        # Displays to user that they have registered successfully
        flash("Account Details Set!")

        # Renders the account page with passed in user account data
        return render_template("account.html", details=rows[0])

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("accountdetails.html", labels=labels)


@app.route("/changepassword",  methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":

        # Ensures all password input was submitted
        if not request.form.get("current") or not request.form.get("password") or not request.form.get("confirmation"):
            flash("Must input all three passwords!")
            return render_template("changepass.html")
        
        # Connects to database
        connection = sqlite3.connect("database.db") 
  
        # SQL Cursor
        cursor = connection.cursor()

        # Query database for username
        cursor.execute("SELECT * FROM users WHERE id = ?", [session["user_id"]])
        rows = cursor.fetchall()

        # Ensures current password is correct
        if not check_password_hash(rows[0][2], request.form.get("current")):
            flash("Invalid current password!")
            return render_template("changepass.html")

        # Hashes the password
        hash = generate_password_hash(request.form.get("password"))

        # Updates database with new password for the user
        sql_command = "UPDATE users SET hash=? WHERE id=?"
        cursor.execute(sql_command, [hash, session["user_id"]])

        # Pushes changes to database
        connection.commit()
        connection.close()

        return redirect("/account")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("changepass.html")

@app.route("/",  methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("Must provide username!")
            return render_template("login.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Must provide password!")
            return render_template("login.html")
        
        # Connects to database
        connection = sqlite3.connect("database.db") 
  
        # SQL Cursor
        cursor = connection.cursor()

        # Query database for username
        cursor.execute("SELECT * FROM users WHERE username = ?", [request.form.get("username")])
        rows = cursor.fetchall()

        # Ensure username exists and password is correct
        if not rows or not check_password_hash(rows[0][2], request.form.get("password")):
            flash("Invalid username and/or password!")
            return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = rows[0][0]

        connection.close()

        # Redirect user to about page
        return redirect("/account")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/register",  methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("Must provide username!")
            return render_template("register.html")

        # Ensure password was submitted
        elif not request.form.get("password") or not request.form.get("confirmation"):
            flash("Must provide username!")
            return render_template("register.html")

        # Ensure password and password confirmation are equal
        elif request.form.get("password") != request.form.get("confirmation"):
            flash("Passwords do not match!")
            return render_template("register.html")

        username = request.form.get("username")

        # Hashes the password
        hash = generate_password_hash(request.form.get("password"))

        # Connects to database
        connection = sqlite3.connect("database.db") 
  
        # SQL Cursor
        cursor = connection.cursor()

        # Query database to see if username already exists
        cursor.execute("SELECT * FROM users WHERE username = ?", [request.form.get("username")])
        rows = cursor.fetchall()

        # Ensures that username does not already exist
        if rows:
            flash("Username is taken!")
            return render_template("register.html")
        
        # Inserts a new user into the SQL database
        cursor.execute("INSERT INTO users (username, hash) VALUES(?, ?)", [username, hash])

        # Selects the newly created user from the SQL database and remembers they have logged in
        cursor.execute("SELECT id FROM users WHERE username = ?", [request.form.get("username")])
        rows = cursor.fetchall()
        session["user_id"] = rows[0][0]
        
        connection.commit()
        connection.close()

        # Redirect user to about page
        return redirect("/accountdetails")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

