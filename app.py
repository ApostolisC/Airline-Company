from flask import Flask, redirect, url_for, request
from flask_pymongo import PyMongo
from pymongo import MongoClient

import os
from argon2 import hash_password_raw
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from uuid import uuid4

"""
steps to create mongodb
 docker pull mongo
 docker run -d -p 27017:27017 --name DigitalAirlines mongo
 docker start DigitalAirlines
 docker exec -it DigitalAirlines mongosh

# TODO:
δημιουργία ιστοσελίδας μετά την είσοδο στο σύστημα

Αλλαγή της προβολής λάθων πεδίων κατά την ενέργεια του signup
δημιουργία ενέργειας αποσύνδεσης (προσθήκη στο navigator)

Δημιουργία worker που θα βγάζει το session key μετά από 30 λεπτά αδράνειας και
θα κάνει reset μετά από κάποια ενέργεια.

"""


def createHash(password):
        ph = PasswordHasher()
        hash = ph.hash(password)
        return hash

def verifyHash(hash, password):
    ph = PasswordHasher()
    try:
        ph.verify(hash, password)
    except VerifyMismatchError:
        return False
    return True


app = Flask(__name__)
app.config["MONGO_URI"] = 'mongodb://' + "localhost" + ':27017/'
#mongo = PyMongo(app)
#db = mongo.db
#accounts =  db['Accounts']

client = MongoClient('mongodb://localhost:27017/DigitalAirlines')["DigitalAirlines"]
#db = client['DigitalAirlines']
accounts = client["accounts"]
users = client["users"]
sessions = client["sessions"]
flights = client["flights"]


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return open("login.html", "r")
    elif request.method == 'POST':
        try:
            data = request.get_json()

            username = data['username']
            password = data['password']

            account = accounts.find_one({"username": username})

            if not account:
                return {"status": "failure", "message": "User doesn't exist!"}

            hash = account["password"]
            verified = verifyHash(hash, password)

            if not verified:
                return {"status": "failure", "message": "Invalid Credentials!"}

            session_key = str(uuid4())

            sessions.insert_one({"id": account["id"], "session-key": session_key})


            return {"status": "success", "message": "Logged in!", "session-key": session_key}
        except Exception as e:
            print(e)
            return {"status": "failure", "message": "Invalid parameters!"}


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return open("signup.html", "r")
    elif request.method == 'POST':
        try:
            data = request.get_json()

            name = data['name']
            surname = data['surname']
            email = data['email']
            password = data['password']
            birth_date = data['dob']
            country_of_origin = data['coo']
            passport_number = data['passport']

            user_exists = accounts.find_one({"username": email})
            print("\nUser exists:",user_exists)

            if user_exists:
                return {"status": "failure", "message": "Email already exists!"}


            exists = accounts.find_one({"username": email})

            #add user to database
            hash = createHash(password)
            id = str(uuid4())

            login_info = {'id': id, "username": email, "password": hash}

            user_info = {'id': id, 'name': name, 'surname': surname, 'email': email, 'birth_date': birth_date, 'country_of_origin': country_of_origin, 'passport': passport_number}

            accounts.insert_one(login_info)
            users.insert_one(user_info)

            session_key = str(uuid4())
            sessions.insert_one({"id": id, "session-key": session_key})


            return {"status": "success", "message": "Account created!", "session-key": session_key}
        except Exception as e:
            print("eRROR:",e)
            return {"status": "failure", "message": "Invalid parameters!"}
        finally:
            print("done")

@app.route('/signout', methods=['POST'])
def signout():
    data = request.get_json()
    try:
        username = data["username"]
        session_key = data["session-key"]
    except KeyError:
        return {"status": "failure", "message": "Invalid parameters"}


    id = accounts.find_one({"username": username})
    if not id:
        return {"status": "failure", "message": "Invalid parameters"} # cant find account

    pair = sessions.find_one({"id": id["id"], "session-key": session_key})
    if not pair:
        return {"status": "failure", "message": "Invalid parameters"} # cant find pair (id, session-key)

    sessions.delete_one({"id": id["id"], "session-key": session_key})

    return {"status": "success", "message": "Session terminated!"}


@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    print(data)

    try:
        airport_from = data["airport-origin"]
        airport_to = data["airport-destination"]
        date = data["date"]
    except KeyError:
        return {"status": "failure", "message": "Invalid parameters"}

    """
    data validation
    """

    a=0
    if airport_from: a+=1
    if airport_to: a+=2
    if date: a+=4

    """
    Our data are valid only when:
        1. We have all 3 parameters
        2. Only the airports origin-destination
        3. Only date
        4. All 3 are blank

    based on the above sum, the a will have value per situation as:
        1. 1+2+4 = 7
        2. 1+2 = 3
        3. 4
        4. 0
    Every other value of a means invalid data
    """
    if a not in (0,3,4,7):
        return {"status": "failure", "message": "Invalid parameters"}

    search = {}
    # if a == 0 then search filter is ready

    if a in (1,2):
        search["airport-origin"] = airport_from
        search["airport-destination"] = airport_to

    if a in (1,3):
        search["date"] = date

    records = flights.find(search)
    records.pop("_id")

    return records


@app.route('/flight/<id>', methods=['GET'])
def get_flight(id):
    pass

@app.route('/reservation', methods=['POST'])
def create_reservation():
    pass

@app.route('/reservations', methods=['POST'])
def get_reservation():
    pass

@app.route('/cancel', methods=['POST'])
def cancel_reservation():
    pass

@app.route('/accountDel', methods=['GET'])
def delete_account():
    pass

@app.route('/', methods=['GET'])
def serve_start():
    # later change to index.html and create it
    return(open("index.html","r"))

if __name__ == '__main__':
    app.run(debug=True, port=8080)
