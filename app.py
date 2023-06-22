from flask import Flask, redirect, url_for, request, abort, jsonify
from flask_pymongo import PyMongo
from pymongo import MongoClient

import os
from argon2 import hash_password_raw
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from uuid import uuid4

import uuid
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
| SingoutUser           |           yes            |
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
| search                |           yes            |
|--------------------------------------------------|
| get_flight            |           yes            |
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
| sys_signout           |           yes            |
|--------------------------------------------------|
| create_flight         |           yes            |
|--------------------------------------------------|
| update_flight_cost    |           yes            |
|--------------------------------------------------|
| delete_flight         |           yes            |
|--------------------------------------------------|
| search_flights        |           yes            |
|--------------------------------------------------|
| flight_info           |           yes            |
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

admins = client["admins"]
admin_sessions = client["admin_sessions"]
accounts = client["accounts"]
users = client["users"]
sessions = client["sessions"]
flights = client["flights"]
reservations = client["reservations"]

permitted_endpoints_for_user = ("login", "signup", "signout", "search", "flight", "reservations", "reservation", "cancel", "account-delete")



def validateSessionKey(username, session_key, admin=False):
    sessions_db = sessions if not admin else admin_sessions
    accounts_db = accounts if not admin else admins

    id = accounts_db.find_one({"username": username})
    if not id: return False # cant find account

    pair = sessions_db.find_one({"id": id["id"], "session-key": session_key})
    if not pair: return False # cant find pair (id, session-key)

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

    (sessions if not admin else admin_sessions).insert_one(info)

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
        session_key = authenticated_info["session-key"]
        return {"status": "success", "message": "Logged in!", "session-key": session_key}

def SingoutUser(username, session_key, admin=False):
    validated_session_key = validateSessionKey(username, session_key, admin=admin)
    if not validated_session_key:
        abort(403)
    else:
        id = validated_session_key["id"]
        sessions.delete_one({"id": id["id"], "session-key": session_key})

    return {"status": "success", "message": "Session terminated!"}
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
            country_of_departure = data['coo']
            passport_number = data['passport']

            user_exists = accounts.find_one({"username": email})

            if user_exists:
                return {"status": "failure", "message": "Email already exists!"}


            exists = accounts.find_one({"username": email})

            #add user to database
            hash = createHash(password)
            id = str(uuid4())

            login_info = {'id': id, "username": email, "password": hash}

            user_info = {'id': id, 'name': name, 'surname': surname, 'email': email, 'birth_date': birth_date, 'country_of_departure': country_of_departure, 'passport': passport_number}

            accounts.insert_one(login_info)
            users.insert_one(user_info)

            session_key = str(uuid4())
            sessions.insert_one({"id": id, "session-key": session_key})


            return {"status": "success", "message": "Account created!", "session-key": session_key}
        except Exception as e:
            return {"status": "failure", "message": "Invalid parameters!"}

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
        abort(403)
    else:
        id = validated_session_key["id"]


    sessions.delete_one({"id": id, "session-key": session_key})

    return {"status": "success", "message": "Session terminated!"}

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()

    try:
        username = data["username"]
        session_key = data["session-key"]

        keys = str(data.keys())

        admin = True if "admin-search" in keys else False
        validated_session_key = validateSessionKey(username, session_key, admin=admin)
        if not validated_session_key:
            abort(403)
        else:
            user_id = validated_session_key["id"]


    except KeyError:
        return {"status": "failure", "message": "Invalid parameters"}

    """
    data validation
    """

    a=0
    if "departure-airport" in keys: a+=1
    if "destination-airport" in keys: a+=2
    if "date" in keys: a+=4

    """
    Our data are valid only when:
        1. We have all 3 parameters
        2. Only the airports departure-destination
        3. Only date
        4. All 3 are blank

    based on the above sum, the a will have value per situation as:
        1. 1+2+4 = 7
        2. 1+2 = 3
        3. 4
        4. 0
    Every other value of a means invalid data
    """
    print(a)
    if a not in (0,3,4,7):
        return {"status": "failure", "message": "Invalid parameters"}

    search = {}

    if a in (3, 7):
        search["departure-airport"] = data["departure-airport"]
        search["destination-airport"] = data["destination-airport"]

    if a in (4, 7):
        search["date"] = data["date"]

    records = flights.find(search, {"_id": 0})
    result = []

    for f in records:
        result.append(f)

    print("\n\n\nrecords:",result)

    return jsonify({"flights": result})

@app.route('/flight', methods=['POST'])
def get_flight():
    data = request.get_json()

    try:
        username = data["username"]
        session_key = data["session-key"]
        validated_session_key = validateSessionKey(username, session_key)
        if not validated_session_key:
            abort(403)
        else:
            user_id = validated_session_key["id"]

        flight_id = data["flight-id"]

        record = list(flights.find({"flight-id": flight_id}, {"_id": 0}))
        if record: record=record[0]


        return record

    except KeyError:
        return {"status": "failure", "message": "Invalid parameters"}


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
            abort(403)
        else:
            user_id = validated_session_key["id"]

    except KeyError:
        return {"status": "failure", "message": "Invalid parameters"}

    reservations = reservations.find({"user-id": user_id}, {"_id": 0})

    return reservations

@app.route('/reservation-info', methods=['POST'])
def get_reservation_info():
    pass

@app.route('/cancel', methods=['POST'])
def cancel_reservation():
    data = request.get_json()
    try:
        username = data["username"]
        session_key = data["session-key"]
        validated_session_key = validateSessionKey(username, session_key)
        if not validated_session_key:
            abort(403)
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
            abort(403)
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
    data = request.get_json()
    try:
        username = data["username"]
        session_key = data["session-key"]
    except KeyError:
        return {"status": "failure", "message": "Invalid parameters"}

    validated_session_key = validateSessionKey(username, session_key, admin=True)
    if not validated_session_key:
        abort(403)
    else:
        id = validated_session_key["id"]

    admin_sessions.delete_one({"id": id, "session-key": session_key})

    return {"status": "success", "message": "Session terminated!"}

@app.route('/create-flight', methods=['POST'])
def create_flight():
    """
    Flight Information required:
    -> Departure airport
    -> destination airport
    -> date
    -> # available tickets business
    -> # available tickets economy
    -> cost business
    -> cost economy
    """
    data = request.get_json()
    try:
        username = data["username"]
        session_key = data["session-key"]
        validated_session_key = validateSessionKey(username, session_key, admin=True)
        if not validated_session_key:
            abort(403)


        departure_airport = data["departure-airport"]
        destination_airport = data["destination-airport"]
        date = data["date"]
        number_of_tickets_business = data["total-tickets-business"]
        number_of_tickets_economy = data["total-tickets-economy"]
        cost_business = data["business-cost"]
        cost_economy = data["economy-cost"]
    except KeyError:
        return {"status": "failure", "message": "Invalid parameters"}

    flights.insert_one({"flight-id": str(uuid.uuid1())[0:18],
                        "departure-airport": departure_airport,
                        "destination-airport": destination_airport,
                        "date": date,
                        "total-tickets-business": number_of_tickets_business,
                        "total-tickets-economy": number_of_tickets_economy,
                        "business-cost": cost_business,
                        "economy-cost": cost_economy,
                        "available-tickets-business": number_of_tickets_business,
                        "available-tickets-economy": number_of_tickets_economy
                        })

    return {"status": "success", "message": "Flight created!"}

@app.route('/update-flight-cost', methods=['POST'])
def update_flight_cost():
    data = request.get_json()
    try:
        username = data["username"]
        session_key = data["session-key"]
        validated_session_key = validateSessionKey(username, session_key, admin=True)
        if not validated_session_key:
            abort(403)

        costs = data["new-costs"]

        keys = list(costs.keys())

        a=0
        for v in keys:
            if not v in ("business-cost", "economy-cost"): a+=1

        if a or not keys:
            return {"status": "failure", "message": "Invalid parameters"}

        flight_id = data["flight-id"]

        query = {"flight-id": flight_id}
        new_values = {"$set": {}}


        for v in keys:
            new_values["$set"][v] = str(costs[v])

        a=flights.update_one(query, new_values)

        return {"status": "success", "message": "Updated flight costs"}

    except KeyError:
        return {"status": "failure", "message": "Invalid parameters"}

@app.route('/delete-flight', methods=['POST'])
def delete_flight():
    data = request.get_json()
    try:
        username = data["username"]
        session_key = data["session-key"]
        validated_session_key = validateSessionKey(username, session_key, admin=True)
        if not validated_session_key:
            abort(403)

        flight_id = data["flight-id"]

        flight = flights.find_one({"flight-id": flight_id})
        if not flight:
            return {"status": "failure", "message": "Flight doesn't exist"}

        reservations_exist = reservations.find_one({"flight-id": flight_id})

        if not reservations_exist:
            flights.delete_one({"flight-id": flight_id})
            return {"status": "success", "message": "Deleted flight!"}
        else:
            return {"status": "failure", "message": "Flight has active reservations!"}


    except KeyError:
        return {"status": "failure", "message": "Invalid parameters"}

@app.route('/search-flights', methods=['POST'])
def search_flights():
    data = request.get_json()
    try:
        username = data["username"]
        session_key = data["session-key"]
        validated_session_key = validateSessionKey(username, session_key, admin=True)
        if not validated_session_key:
            abort(403)

        flight_id = data["flight-id"]

        reservations_exist = reservations.find_one({"flight-id": flight_id})

        if not reservations_exist:
            flight.delete_one({"flight-id": flight_id})
            return {"status": "success", "message": "Updates flight costs"}
        else:
            return {"status": "failure", "message": "Flight has active reservations!"}


    except KeyError:
        return {"status": "failure", "message": "Invalid parameters"}

@app.route('/flight-info', methods=['POST'])
def flight_info():
    data = request.get_json()
    try:
        username = data["username"]
        session_key = data["session-key"]
        validated_session_key = validateSessionKey(username, session_key, admin=True)
        if not validated_session_key:
            abort(403)

        flight_id = data["flight-id"]

        flight = flights.find_one({"flight-id": flight_id}, {"_id": 0})

        if not flight:
            return {"status": "failure", "message": "Flight doesn't exist!"}

        flight["total-tickets"] = flight["total-tickets-business"] + flight["total-tickets-economy"]
        flight["total-available-tickets"] = flight["available-tickets-business"] + flight["available-tickets-economy"]

        flight["reservations"] = []

        #flight.pop("date") # to remove the date because date isnt in the assignments description

        return flight


    except KeyError:
        return {"status": "failure", "message": "Invalid parameters"}



@app.route('/', methods=['GET'])
def serve_start():
    # later change to index.html and create it
    return(open("index.html","r"))

if __name__ == '__main__':
    app.run(debug=True, port=8080)
