# Containerized flask and mongodb services

# Introduction
The purpose of the specific project is the creation of an information system for the provision of services similar to an airline company. Mongodb is used to maintain the necessary data and flask service for the interface between a client and the database, while these 2 services then run in a common container.

# Terminology
<h4>Client</h4>
The system responsible for the communication between the flask server and the end user.

<h4>Endpoint</h4>
The path provided after the original (main) url. The purpose of the endpoint is to map different paths to different actions.

<h4>Collection</h4>
This project uses Mongodb. Mongodb does not have tables as sql. but have instead collections that are just json formatted data.

<h4>Admin</h4>
Admin or administrator is a role that can have access to the inside functions of the system. In our case the administrator is able to alter collections to create or delete data.

<h4>Regular user - Simple user</h4>
The person (or end user) that uses the services provided by the client and the flask server.

# Database and Collections
There are 7 collections inside the DigitalAirlines database. 
* admins
* accounts
* users
* admin_sessions
* sessions
* flights
* reservations

Admin collection contains an ID, unique to the admin, along with the username and the password.
The password is an argon hash ensuring secure identification.

Accounts collection is the same as admin collection with the only difference being that it is used to connect simple users.

Users collection is linked with the accounts collection complementing each other. 
It contains:
* ID of the user
* Name
* Surname
* Email
* Birth date
* Country of origin
* Passport number

Admin_sessions is the collection holding the sessions for administrators. When an administrator logs in, a new record is created containing the ID of the admin account along with a random session key.
Whenever the administrator wants to perform an operation with administrator rights, he must provide the relevant session key to authenticate him.

Sessions collection is the same as the admin_sessions but for the purpose of holding session keys for simple users.

Flights collection contains all required information about a flight to be performed. The information of each flight is:
* Flight id
* Departure Airport
* Destination Airport
* Date of the flight
* Total tickers for business class
* Total tickets for economy class
* Cost for business class
* Cost for economy class
* Available tickets for business class
* Available tickets for economy class

Where flight id a random generated uuid.

Reservations collection maintains the bookings that users have made for a particular flight.
The information inside the collection is:
* User id
* Flight id
* Reservation id
* Name
* Surname
* Passsport number
* Date of birth
* email
* Class (business or economy)

<h3>Note</h3>
All the ID fields inside collections are a custom uuid, instead of an ObjectId mongodb creates.
This implementation allows us to change the ID structure to suit our needs.

# Security
Βy having 2 different collections to keep session keys for ordinary users and administrators, we are sure that an ordinary user will not be able to perform an administrator function, since an administrator session key is required, which requires an administrator account login. By isolating users from administrators we ensure the integrity of the services for this potential risk. 
Also, regarding the authentication mechanism, the password is stored as an argon2 hash, ensuring the confidentiality of the password.

The connection between the flask server and client is not encrypted using https.
<br> <b>DO NOT</b> use on unsafe networks. 

# Usage
Τhe project is split into 2 parts, with the first being the functions for regular users and and the second for administrators.
<br>
We will start with the Admin functions, since regular user's functions need some knowledge of the format the data are stored as.

<h2>Admin functions</h2>

<h4>Signup</h4>
Τhere is no administrator signup function, since mongo database requirements require an administrator with manual entry.

<h4>Login</h4>
An administrator is able to perform login function by visiting <b>/sys-login</b> endpoint.
Τhe required fields are the name and password.
<br>
<pre>
{ 
  "username": "admin_username",
  "password": "admin_password"
}
</pre>
Response:
<br>
<pre>
{
  "message": "Logged in!",
  "session-key": "a0202fea-c05c-4991-8945-dde57c080eb5",
  "status": "success"
}
</pre>

<h4>For the rest of the functions it is also necessary to grant the session-key</h4>

<h4>Signout</h4>
An admin can signout by visiting <b>/sys-signout</b> endpoint, providing the following information:
<br>
<pre>
{
  "username": "admin_username",
  "session-key": "session-key"
}
</pre>
The result will be the removal of the provided session-key from admin_sessions collection, with the admin not being able to perform actions without logging in again.

<h4>Create Flight</h4>
Admin can create a flight using <b>/create-flight</b> endpoint providing the following information:
<br>
<pre>
{
  "departure-airport": "Athens",
  "destination-airport": "Stockholm",
  "date": "27/12/2023"
  "total-tickets-business": 51
  "total-tickets-economy": 138
  "business-cost": "646",
  "economy-cost": "206"
}
</pre>

Response:
<br>
<pre>
{
  "status": "success", 
  "message": "Flight created!"
}
</pre>

<h4>Update flight cost</h4>
Using endpoint <b>/update-flight-cost</b> the admin is able to update the cost for economy and business tickets.
The message format must be as follows:
<br>
<pre>
{
  "new-costs": {
                  "business-cost": "new_cost",
                  "economy-cost": "new_cost"
                }
}
</pre>

Response:
<br>
<pre>
{
  "status": "success", 
  "message": "Updated flight costs"
}
</pre>


<h4>Delete flight</h4>
By visiting <b>/delete-flight</b> endpoint the admin will be able to delete a flight from the database.
He only needs to provide the flight id.

Request message:
<br>
<pre>
{
  "username": "admin_username",
  "session-key": "session-key",
  "flight-id": "flight_id"
}
</pre>

If there are reservations for this flight, then the deletion will fail, with the admin getting the following response:
<br>
<pre>
{
  "status": "failure", 
  "message": "Flight has active reservations!"
}
</pre>

And in case the flight doesn't exist:
<br>
<pre>
{
  "status": "failure", 
  "message": "Flight doesn't exist"
}
</pre>

At last the normal response would be as follows:
<br>
<pre>
{
  "status": "success", 
  "message": "Deleted flight!"
}
</pre>

<h4>Search flights</h4>
The search function is the same for both admins and normal users.
The only difference is that the admin must provide a keyword "admin-search": True so the server will know and try to validate his session key from admin_sessions and not sessions.
The endpoint is <b>/search</b>.

Then he may provide 3 more fields:
* Departure airport
* Destination airport
* Date

The search will be possible only if:
1. Both departure and destination airports are provided
2. Only date id provided
3. All fields are provided
4. None of the fields is provided

The format for the above states are as follows:

1. Both departure and destination airports are provided
<br>
<pre>
{
  "username": "admin_username",
  "session-key": "admin_session_key",
  "departure-airport": "Athens",
  "destination-airport": "Stockholm"
}
</pre>

2. Only date is provided
<br>
<pre>
{
  "username": "admin_username",
  "session-key": "admin_session_key",
  "date": "27/12/2023"
}
</pre>

3. All fields are provided
<br>
<pre>
{
  "username": "admin_username",
  "session-key": "admin_session_key",
  "departure-airport": "Athens",
  "destination-airport": "Stockholm",
  "date": "27/12/2023"
}
</pre>

4. None of the fields is provided (Return all available flights)
<br>
<pre>
{
  "username": "admin_username",
  "session-key": "admin_session_key"
}
</pre>

</pre>
<h4>Search flight information</h4>
By visiting <b>/flight-info</b> and providing the flight-id admin is able to retrieve flight information.

Request format:
<br>
<pre>
{
  "username": "admin_username",
  "session-key": "session-key",
  "flight-id": "flight_id"
}
</pre>

Response:
<br>
<pre>
{
  "flight-id": "flight_id",
  "departure-airport": "Athens",
  "destination-airport": "Stockholm",
  "date": "27/12/2023",
  "total-tickets-business": "51",
  "total-tickets-economy": "138",
  "business-cost": "646",
  "economy-cost": "206",
  "available-tickets-business": "51",
  "available-tickets-economy": "138",
  "total-tickets": "189",
  "total-available-tickets": "189"
}
</pre>


<h2>User functions</h2>

<h4>Login</h4>
User is able to login by visiting <b>/login</b> endpoint and provide the following information:
<br>
<pre>
{
  "username": "users_email"
  "password": "password"
}  
</pre>

Response:
<br>
<pre>
{
  "message": "Logged in!",
  "session-key": "e3083174-cb85-4362-b2cc-edd271ba9710",
  "status": "success"
}
</pre>

<h4>Signup</h4>
User can create an account via <b>/signup</b> endpoint, providing the following information:
* Name
* Surname
* Email
* Password
* Date of birth
* Country of origin
* Passport number

The format must be as follows:
<br>
<pre>
{
  "name": "name1",
  "surname": "surname1",
  "email": "email1",
  "password": "password1",
  "dob": "xx/yy/zzz",
  "coo": "country1"
  "passport": "passport1"
}
</pre>

Response:
<br>
<pre>
{
  "status": "success", 
  "message": "Account created!", 
  "session-key": session_key
}
</pre>
Now user is already logged in with his own session-key.
<br> If the provided email already exists then the signup will fail, with the user getting the response:
<br>
<pre>
{
  "status": "failure",
  "message": "Email already exists!"
}
</pre>

<h4>Signout</h4>
User can signout from his session by visiting <b>/signout</b> endpoint and provide the following request:
<br>
<pre>
{
  "username": "username1",
  "session-key": "e3083174-cb85-4362-b2cc-edd271ba9710"
}
</pre>
After that action, user will not be able to perform any actions before he performs login again.

<h4>Search flights</h4>
The function is the same for regular users and admins.
The only difference is that the admin must also provide a keyword admin-search
The format for the above states are as follows:

1. Both departure and destination airports are provided
<br>
<pre>
{
  "username": "username",
  "session-key": "session_key",
  "departure-airport": "Athens",
  "destination-airport": "Stockholm"
}
</pre>

2. Only date is provided
<br>
<pre>
{
  "username": "username",
  "session-key": "session_key",
  "date": "27/12/2023"
}
</pre>

3. All fields are provided
<br>
<pre>
{
  "username": "username",
  "session-key": "session_key",
  "departure-airport": "Athens",
  "destination-airport": "Stockholm",
  "date": "27/12/2023"
}
</pre>

4. None of the fields is provided (Return all available flights)
<br>
<pre>
{
  "username": "username",
  "session-key": "session_key"
}
</pre>

<h4>Flight information</h4>
By visiting <b>/flight</b> endpoint user will be able to retrieve information about a specific flight.
Requirements are the flight id.

Request format:
<br>
<pre>
{
  "username": "username",
  "session-key": "session_key",
  "flight-id": "flight-id"
}
</pre>

<h4>Flight reservation</h4>
To create a flight reservation, user must submit the following information on <b>/flight-reservation</b> endpoint.
* Name
* Surname
* Passport number
* Date of birth
* Email
* Reservation class

Request format:
<br>
<pre>
{
  "name": "name1",
  "surname": "surname1:,
  "passport-number": "passport_number1",
  "dob": "xx/yy/zzz",
  "email": "email1",
  "reservation-class": "class"
}
</pre>
The reservation class will either be business or economy.


<h4>Reservations retrieving</h4>
To retrieve all reservations, user will visit <b>/reservations</b> endpoint with only information his username and session-key as follows:
<br>
<pre>
{
  "username": "username1",
  "session-key": "session-key"
}
</pre>

<h4>Reservation's information retrieving</h4>
To retrieve reservation's information along with flight information attached to the reservation, user will visit <b>/reservation-info</b> endpoint providing the following values:
<br>
<pre>
{
  "username": "username1",
  "session-key": "session-key",
  "reservation-id": "reservation_id"
</pre>

The returned result will contain:
* Departure airport
* Destination airport
* Date of the flight
* Name
* Surname
* Passport number
* Date of birth
* Email
* Reservation class
  
<h4>Reservation cancelation</h4>
Client can cancel his reservation by visiting <b>/cancel</b> endpoint, providing the reservation id to be canceled.

Format:
<br>
<pre>
{
  "username": "username1",
  "session-key": "session_key",
  "reservation-id": "reservation_id"
}
</pre>

If the reservation doesn't exist an appropriate return message will be received.

<h4>Account deletion</h4>
Client can delete user's account via <b>/account-delete</b> endpoint providing only the username and the session-key.
Format:
<br>
<pre>
{
  "username": "username1",
  "session-key": "session_key"
}
</pre>

# Containerization 
We have the following path format:

* flask
    * data
    * service.py
    * Dockerfile
    * requirements.txt
* mongodb
    * data
* docker-compose.yml

Step 1.
<br>First of all we need to download the official mongodb image.
<pre>
docker pull mongo
</pre>

<br>Step2
<br>Now inside the base path where the docker-compose.yml file exists we will run the following command to create the image:
<pre>
docker-compose build
</pre>

<br>Step3
<br>Now we will run the container that contains both mongodb and flask server
<pre>
docker-compose up -d
</pre>

<br><b>At this point we can access the flask server from localhost:5000</b>
