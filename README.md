# Containerized flask and mongodb services

# Introduction
The purpose of the specific project is the creation of an information system for the provision of services similar to an airline company. Mongodb is used to maintain the necessary data and flask service for the interface between a client and the database, while these 2 services then run in a common container.

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

<h5>Note</h5>
Βy having 2 different collections to keep session keys for ordinary users and administrators, we are sure that an ordinary user will not be able to perform an administrator function, since an administrator session key is required, which requires an administrator account login. By isolating users from administrators we ensure the integrity of the services for this potential risk.

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

# Usage
Τhe project is split into 3 parts, with 2 being functions for regular users and administrators, and the third being functions that provide support for the other 2 parts

<h2>Admin functions</h2>

<h4>Signup</h4>
Τhere is no administrator signup function, since mongo database requirements require an administrator with manual entry.

<h4>Login</h4>
An administrator is able to perform login function by visiting /sys-login endpoint.
Τhe required fields are the name and password.
<pre>
{ 
  "username": "admin_username",
  "password": "admin_password"
}
</pre>
Response:
<pre>
{
  "message": "Logged in!",
  "session-key": "a0202fea-c05c-4991-8945-dde57c080eb5",
  "status": "success"
}
</pre>

<h4>For the rest of the functions it is also necessary to grant the session-key</h4>

<h4>Signout</h4>
An admin can signout by visiting /sys-signout endpoint, providing the following information:
<pre>
  {
    "username": "admin_username",
    "session-key": "session-key"
  }
</pre>
The result will be the removal of the provided session-key from admin_sessions collection, with the admin not being able to perform actions without logging in again.

<h4>Create Flight</h4>
Admin can create a flight using /create-flight endpoint providing the following information:
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

