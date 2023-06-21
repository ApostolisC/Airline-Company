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


Δημιουργία worker που θα βγάζει το session key μετά από 30 λεπτά αδράνειας και
θα κάνει reset μετά από κάποια ενέργεια.


TESTED:

GENERAL FUNCTIONS
|--------------------------------------------------|
|       Function        |         Tested           |
|--------------------------------------------------|
| validateSessionKey    |           yes            |
|--------------------------------------------------|
| LoginUser             |           yes            |
|--------------------------------------------------|
| createLoginError      |           yes            |
|--------------------------------------------------|

USER
|--------------------------------------------------|
|       Function        |         Tested           |
|--------------------------------------------------|
| login                 |           yes            |
|--------------------------------------------------|
| signup                |           yes            |
|--------------------------------------------------|
| signout               |           yes            |
|--------------------------------------------------|
| search                |                          |
|--------------------------------------------------|
| get_flight            |                          |
|--------------------------------------------------|
| flight_reservation    |           no             |
|--------------------------------------------------|
| get_reservations      |                          |
|--------------------------------------------------|
| get_reservation_info  |           no             |
|--------------------------------------------------|
| cancel_reservation    |                          |
|--------------------------------------------------|
| delete_account        |           yes            |
|--------------------------------------------------|

ADMIN
|--------------------------------------------------|
|       Function        |         Tested           |
|--------------------------------------------------|
| sys_login             |           yes            |
|--------------------------------------------------|
| sys_signout           |                          |
|--------------------------------------------------|
| create_flight         |                          |
|--------------------------------------------------|
| update_flight         |                          |
|--------------------------------------------------|
| delete_flight         |                          |
|--------------------------------------------------|
| search_flights        |                          |
|--------------------------------------------------|
| flight_info           |                          |
|--------------------------------------------------|

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


client = MongoClient('mongodb://localhost:27017/DigitalAirlines')["DigitalAirlines"]

accounts = client["accounts"]
users = client["users"]
sessions = client["sessions"]
flights = client["flights"]
reservations = client["reservations"]
admins = client["admins"]

permitted_endpoints_for_user = ("login", "signup", "signout", "search", "flight", "reservations", "reservation", "cancel", "account-delete")

def validateSessionKey(username, session_key):
    id = accounts.find_one({"username": username})
    print("validation returned:",id)
    if not id:
        return False # cant find account

    pair = sessions.find_one({"id": id["id"], "session-key": session_key})
    if not pair:
        return {"status": "failure", "message": "Invalid parameters"} # cant find pair (id, session-key)

    return {"id": id["id"], "session-key": session_key}

def LoginUser(username, password, admin=False):
    """
    To reuse on both login and sys-login
    """
    database = accounts if not admin else admins

    account = database.find_one({"username": username})

    if not account: return createLoginError(None)

    hash = account["password"]
    verified = verifyHash(hash, password)
    if not verified: return createLoginError(False)

    session_key = str(uuid4())
    info = {"id": account["id"], "session-key": session_key}

    sessions.insert_one(info)

    return createLoginError(info)

def createLoginError(authenticated_info):
    """
    To reuse on both login and sys-login
    """
    if authenticated_info==None:
        return {"status": "failure", "message": "Account doesn't exist!"}
    elif authenticated_info==False:
        return {"status": "failure", "message": "Invalid Credentials!"}
    else:
        session_key = authenticated_info["id"]
        return {"status": "success", "message": "Logged in!", "session-key": session_key}
"""
User functions
"""
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return open("login.html", "r")
    elif request.method == 'POST':
        try:
            data = request.get_json()

            username = data['username']
            password = data['password']

            authenticated_action = LoginUser(username, password)

            return authenticated_action

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

    validated_session_key = validateSessionKey(username, session_key)
    if not validated_session_key:
        return {"status": "failure", "message": "Invalid parameters"}
    else:
        id = validated_session_key["id"]


    sessions.delete_one({"id": id["id"], "session-key": session_key})

    return {"status": "success", "message": "Session terminated!"}

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    print(data)

    try:
        username = data["username"]
        session_key = data["session-key"]
        validated_session_key = validateSessionKey(username, session_key)
        if not validated_session_key:
            return {"status": "failure", "message": "Invalid parameters"}
        else:
            user_id = validated_session_key["id"]


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

@app.route('/flight', methods=['POST'])
def get_flight():
    data = request.get_json()

    try:
        username = data["username"]
        session_key = data["session-key"]
        validated_session_key = validateSessionKey(username, session_key)
        if not validated_session_key:
            return {"status": "failure", "message": "Invalid parameters"}
        else:
            user_id = validated_session_key["id"]

        flight_id = data["flight-id"]

    except KeyError:
        return {"status": "failure", "message": "Invalid parameters"}

    record = flights.find({"_id":flight_id})
    if not record:
        return {"status": "failure", "message": "Flight doesn't exist!"}

    return record

@app.route('/flight-reservation', methods=['POST'])
def flight_reservation():
    pass

@app.route('/reservations', methods=['POST'])
def get_reservations():
    data = request.get_json()
    try:
        username = data["username"]
        session_key = data["session-key"]
        validated_session_key = validateSessionKey(username, session_key)
        if not validated_session_key:
            return {"status": "failure", "message": "Invalid parameters"}
        else:
            user_id = validated_session_key["id"]

    except KeyError:
        return {"status": "failure", "message": "Invalid parameters"}

    reservations = reservations.find({"user-id": user_id})

    return reservations

@app.route('/reservation-info', methods=['POST'])
def get_reservation_info():
    pass

@app.route('/reservation', methods=['POST'])
def get_reservation():
    data = request.get_json()
    try:
        username = data["username"]
        session_key = data["session-key"]
        validated_session_key = validateSessionKey(username, session_key)
        if not validated_session_key:
            return {"status": "failure", "message": "Invalid parameters"}
        else:
            user_id = validated_session_key["id"]

        reservation_id = data["reservation-id"]

    except KeyError:
        return {"status": "failure", "message": "Invalid parameters"}

    record = reservations.find({"_id": reservation_id})

    return record

@app.route('/cancel', methods=['POST'])
def cancel_reservation():
    data = request.get_json()
    try:
        username = data["username"]
        session_key = data["session-key"]
        validated_session_key = validateSessionKey(username, session_key)
        if not validated_session_key:
            return {"status": "failure", "message": "Invalid parameters"}
        else:
            user_id = validated_session_key["id"]

        reservation_id = data["reservation-id"]

    except KeyError:
        return {"status": "failure", "message": "Invalid parameters"}

    reservations.delete_one({"_id": reservation_id})

    """
    Also update available flights
    """

@app.route('/account-delete', methods=['POST'])
def delete_account():
    data = request.get_json()
    try:
        username = data["username"]
        session_key = data["session-key"]
        validated_session_key = validateSessionKey(username, session_key)
        if not validated_session_key:
            return {"status": "failure", "message": "Invalid parameters"}
        else:
            user_id = validated_session_key["id"]

    except KeyError:
        return {"status": "failure", "message": "Invalid parameters"}

    accounts.delete_one({"id": user_id})
    users.delete_one({"id": user_id})

    return {"status": "success", "message": "Account deleted!"}


"""
Admin functions
"""
@app.route('/sys-login', methods=['POST'])
def sys_login():
    try:
        data = request.get_json()

        username = data['username']
        password = data['password']

        authenticated_action = LoginUser(username, password, admin=True)

        return authenticated_action

    except Exception as e:
        print(e)
        return {"status": "failure", "message": "Invalid parameters!"}

@app.route('/sys-signout', methods=['POST'])
def sys_signout():
    pass

@app.route('/create-flight', methods=['POST'])
def create_flight():
    pass

@app.route('/update-flight', methods=['POST'])
def update_flight():
    pass

@app.route('/delete-flight', methods=['POST'])
def delete_flight():
    pass

@app.route('/search-flights', methods=['POST'])
def search_flights():
    pass

@app.route('/flight-info', methods=['POST'])
def flight_info():
    pass



@app.route('/', methods=['GET'])
def serve_start():
    # later change to index.html and create it
    return(open("index.html","r"))

if __name__ == '__main__':
    app.run(debug=True, port=8080)
