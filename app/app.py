# Import necessary modules
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Ride, Passenger, Satisfaction
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2
import os
import logging

# Initialize the Flask application
app = Flask(__name__, instance_relative_config=True, static_url_path='/static')

# Ensure the instance folder exists
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

# Configure the database to use the instance folder
db_path = os.path.join(app.instance_path, 'user.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'mysecretkey')  # Use environment variable for secret key
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db.init_app(app)

# Set up logging for debugging and error tracking
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Route for home page
@app.route('/')
def home():
    """Render the index page."""
    return render_template('index.html')

# Route for the signup page
@app.route('/signup')
def signup():
    """Render the signup page."""
    return render_template('signup.html')

# Route for user login
@app.route('/login', methods=['GET', 'POST'])
def login_user():
    """Handle user login."""
    if request.method == 'POST':
        if request.is_json:
            # Handle JSON request (e.g., for Insomnia)
            data = request.get_json()  # Retrieve the JSON data
            email = data.get('email')  # Access JSON data
            password = data.get('password')
        else:
            # Handle form submission (e.g., for a browser)
            email = request.form.get('email')  # Access form data
            password = request.form.get('password')

        # Check if email or password is missing
        if not email or not password:
            return jsonify({
                'status': 'error',
                'message': 'Email and password are required.'
            }), 400  # Bad request if fields are missing

        # Query the user by email
        user = User.query.filter_by(email=email).first()

        # Log if the user is found
        if user:
            logger.debug(f"User found: {user.fullname} with email {user.email}")
        else:
            logger.error(f"User not found for email: {email}")

        # If user exists and password matches the hashed password
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id  # Store user ID in session
            session['username'] = user.fullname  # Store username in session
            logger.debug(f"Session Username after login: {session.get('username')}")

            # Handle API requests (like Insomnia)
            if request.is_json:
                return jsonify({
                    'status': 'success',
                    'message': 'Login successful'
                }), 200  # OK

            # Redirect to dashboard for browser-based login
            return redirect(url_for('dashboard'))

        else:
            logger.error("Invalid login attempt: Incorrect email or password.")
            
            # Handle API requests (like Insomnia)
            if request.is_json:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid email or password.'
                }), 401  # Unauthorized

            # For browser-based login, display error
            return render_template('login.html', error='Invalid email or password.')

    # For GET request, render the login page
    return render_template('login.html')

# Route for user registration (signup form submission)
@app.route('/submit', methods=['POST'])
def submit():
    """Handle user registration."""
    try:
        # Check if the request content type is JSON
        if request.is_json:
            data = request.get_json()  # Handle JSON data
        else:
            data = request.form  # Handle form data (for browser)

        # Extract user data from the request
        fullname = data.get('fullname')
        email = data.get('email')
        password = data.get('password')
        CIN = data.get('CIN')
        phone = data.get('phone')

        # Ensure CIN is an integer
        try:
            CIN = int(CIN)  # Convert CIN to an integer
        except ValueError:
            return jsonify({
                'status': 'error',
                'message': 'CIN must be a valid number.'
            }), 400

        # Validate required fields
        if not fullname or not email or not password or not CIN or not phone:
            return jsonify({
                'status': 'error',
                'message': 'All fields must be filled.'
            }), 400      

        # Check if user already exists (by email)
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            # User already exists, return error
            if request.is_json:
                return jsonify({
                    'status': 'error',
                    'message': 'You already have an account. Try signing in.'
                }), 400
            else:
                return render_template('login.html', error='You already have an account. Try signing in.')

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Create new user and add to the database
        user = User(fullname=fullname, email=email, password=hashed_password, CIN=CIN, phone=phone)
        db.session.add(user)
        db.session.commit()

        # Return success message for API requests (like Insomnia)
        if request.is_json:
            return jsonify({
                'status': 'success',
                'message': 'User registered successfully'
            }), 200
        else:
            # Redirect to login page for form submissions (browser)
            return redirect(url_for('login_user'))

    except Exception as e:
        # Rollback database session and log error
        db.session.rollback()
        logger.error(f"Error during registration: {str(e)}")

        return jsonify({
            'status': 'error',
            'message': f'Registration failed: {str(e)}'
        }), 500

        
# Route for Dashboard
@app.route('/dashboard')
def dashboard():
    """Render the dashboard with the user's ride statistics."""
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in

    user_id = session['user_id']

    # Fetch the count of rides offered by the user
    offered_rides_count = db.session.execute(
        "SELECT COUNT(*) FROM ride WHERE creator_id = :user_id",
        {"user_id": user_id}
    ).fetchone()[0]
   
    # Fetch the count of rides joined by the user
    joined_rides_count = db.session.execute(
        "SELECT COUNT(*) FROM Passenger WHERE creator_id = :user_id",
        {"user_id": user_id}
    ).fetchone()[0]
   
    # Return the data to render the dashboard template
    return render_template(
        'dashboard.html',
        username=session['username'],
        offered_rides_count=offered_rides_count,
        joined_rides_count=joined_rides_count,
    )


# Route for Logout
@app.route('/logout')
def logout():
    """Handle user logout."""
    session.pop('user_id', None)  # Remove user_id from session
    return redirect(url_for('login_user'))


# Route for searching rides (GET and POST)
@app.route('/search_ride', methods=['GET', 'POST'])
def search_ride():
    """Handle ride searching."""
    # Handle GET request to fetch all ride data
    if request.method == 'GET':
        try:
            rides = Passenger.query.all()
            rides_data = [{
                "id": ride.id,
                "creator_id": ride.creator_id,
                "departure": ride.departure,
                "departure_coordinates": ride.departure_coordinates,
                "destination": ride.destination,
                "destination_coordinates": ride.destination_coordinates,
                "departure_time": ride.departure_time.isoformat(),
                "trip_type": ride.trip_type,
                "return_time": ride.return_time.isoformat() if ride.return_time else None,
                "return_destination": ride.return_destination,
                "return_destination_coordinates": ride.return_destination_coordinates,
                "preferred_gender": ride.preferred_gender,
                "preferred_music": ride.preferred_music,
                "smoking_preference": ride.smoking_preference,
                "talkative_preference": ride.talkative_preference,
                "pets_allowed": ride.pets_allowed,
                "air_conditioning": ride.air_conditioning,
                "children_allowed": ride.children_allowed,
                "created_at": ride.created_at.isoformat(),
                "updated_at": ride.updated_at.isoformat()
            } for ride in rides]

            # Return JSON data if requested
            if request.is_json or request.headers.get('Accept') == 'application/json':
                return jsonify(rides_data)

            # Render the template with the fetched data
            return render_template('search_ride.html', rides=rides_data)
        
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'Error fetching rides data: {str(e)}'}), 500

    # Handle POST request to create a new ride search
    if 'user_id' not in session:
        if request.is_json:
            return jsonify({'status': 'error', 'message': 'You are not logged in'}), 401
        else:
            return redirect(url_for('login_user'))

    if request.method == 'POST':
        try:
            # Ensure the incoming request is JSON or form data
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form

            # List of required fields for the ride search
            required_fields = [
                'departure-search', 'departure',
                'destination-search', 'destination', 'departure-time',
                'trip-type', 'gender', 'music', 'smoking', 'talkative',
                'pets', 'air_conditioning', 'children'
            ]

            # Check for missing required fields
            missing_fields = [field for field in required_fields if not data.get(field)]
            if missing_fields:
                error_message = f"Missing fields: {', '.join(missing_fields)}"
                if request.is_json:
                    return jsonify({'status': 'error', 'message': error_message}), 400

            # Create new passenger entry for the ride search
            new_passenger = Passenger(
                creator_id=session['user_id'],
                departure=data.get('departure-search'),
                departure_coordinates=data.get('departure'),
                destination=data.get('destination-search'),
                destination_coordinates=data.get('destination'),
                departure_time=datetime.strptime(data.get('departure-time'), '%Y-%m-%dT%H:%M'),
                trip_type=data.get('trip-type'),
                preferred_gender=data.get('gender'),
                preferred_music=data.get('music'),
                smoking_preference=data.get('smoking'),
                talkative_preference=data.get('talkative'),
                pets_allowed=data.get('pets'),
                air_conditioning=data.get('air_conditioning'),
                children_allowed=data.get('children')
            )

            # Handle two-way trips
            if data.get('trip-type') == 'two-way':
                new_passenger.return_time = datetime.strptime(data.get('return-time'), '%Y-%m-%dT%H:%M')
                new_passenger.return_destination = data.get('return-destination-search')
                new_passenger.return_destination_coordinates = data.get('return-destination')

            db.session.add(new_passenger)
            db.session.commit()

            # Return success response
            if request.is_json:
                return jsonify({
                    'status': 'success',
                    'message': 'Ride search successfully created'
                }), 200

            return redirect(url_for('matching'))

        except Exception as e:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': f'Failed to create ride: {str(e)}'}), 500

    # Render search ride template
    return render_template('search_ride.html')


@app.route('/create_ride', methods=['GET', 'POST'])
def create_ride():
    """Handle ride creation."""
    
    if 'user_id' not in session:
        # Check if the request is expecting JSON (for API tools like Insomnia)
        if request.is_json:
            return jsonify({
                'status': 'error',
                'message': 'You are not logged in'
            }), 401  # Unauthorized
        else:
            # Redirect non-API requests to login page
            return redirect(url_for('login_user'))
    
    if request.method == 'POST':
        try:
            # Determine if the request is JSON or standard form submission
            data = request.get_json() if request.is_json else request.form
            
            if not data:
                return jsonify({
                    'status': 'error',
                    'message': 'No data provided'
                }), 400  # Bad Request
            
            # Ensure all required fields are present
            required_fields = [
                'departure-search', 'departure', 'destination-search', 'destination', 
                'departure-time', 'trip-type', 'gender', 'music', 'smoking', 'talkative', 
                'pets', 'air_conditioning', 'children', 'carte-grise', 'car-type', 'Car-Name'
            ]
            missing_fields = [field for field in required_fields if not data.get(field)]
            
            if missing_fields:
                error_message = f"Missing fields: {', '.join(missing_fields)}"
                if request.is_json:
                    return jsonify({
                        'status': 'error',
                        'message': error_message
                    }), 400  # Bad Request
                return render_template('create_ride.html', error=error_message)
            
            # Create the new ride instance
            new_ride = Ride(
                creator_id=session['user_id'],  # Use session user ID
                departure=data.get('departure-search'),
                departure_coordinates=data.get('departure'),
                destination=data.get('destination-search'),
                destination_coordinates=data.get('destination'),
                departure_time=datetime.strptime(data.get('departure-time'), '%Y-%m-%dT%H:%M'),
                trip_type=data.get('trip-type'),
                preferred_gender=data.get('gender'),
                preferred_music=data.get('music'),
                smoking_preference=data.get('smoking'),
                talkative_preference=data.get('talkative'),
                pets_allowed=data.get('pets'),
                air_conditioning=data.get('air_conditioning'),
                children_allowed=data.get('children'),
                carte_grise=data.get('carte-grise'),
                car_type=data.get('car-type'),
                car_name=data.get('Car-Name'),
            )
            
            # Add return trip details if applicable
            if data.get('trip-type') == 'two-way':
                return_time = data.get('return-time')
                return_destination = data.get('return-destination-search')
                return_destination_coordinates = data.get('return-destination')
                if return_time and return_destination and return_destination_coordinates:
                    new_ride.return_time = datetime.strptime(return_time, '%Y-%m-%dT%H:%M')
                    new_ride.return_destination = return_destination
                    new_ride.return_destination_coordinates = return_destination_coordinates
            
            # Add the new ride to the session and commit
            db.session.add(new_ride)
            db.session.commit()
            
            # Return success response
            if request.is_json:
                return jsonify({
                    'status': 'success',
                    'message': 'Ride successfully created'
                }), 200
            
            # Redirect to dashboard after successful creation
            return redirect(url_for('dashboard'))
        
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'status': 'error',
                'message': f'Failed to create ride: {str(e)}'
            }), 500
    
    return render_template('create_ride.html')


@app.route('/users', methods=['GET'])
def get_all_users():
    """Fetch all user information from the database."""
    
    try:
        users = User.query.all()  # Query all users from the database
        
        # Convert user data to a list of dictionaries
        user_data = [{
            'id': user.id,
            'fullname': user.fullname,
            'email': user.email
        } for user in users]
        
        return jsonify({'status': 'success', 'users': user_data}), 200
    
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to retrieve users.'}), 500


@app.before_first_request
def create_database():
    """Ensure the database is created before handling any requests."""
    
    if not os.path.exists(db_path):
        db.create_all()


@app.route('/rides', methods=['GET'])
def get_all_rides():
    """Fetch all rides."""
    
    try:
        rides = Ride.query.all()
        
        # Prepare ride data
        rides_data = [{
            'id': ride.id,
            'creator_id': ride.creator_id,
            'destination': ride.destination,
            'destination_coordinates': ride.destination_coordinates,
            'departure_time': ride.departure_time.isoformat(),
            'trip_type': ride.trip_type,
            'return_time': ride.return_time.isoformat() if ride.return_time else None,
            'return_destination': ride.return_destination,
            'return_destination_coordinates': ride.return_destination_coordinates,
            'preferred_gender': ride.preferred_gender,
            'preferred_music': ride.preferred_music,
            'smoking_preference': ride.smoking_preference,
            'talkative_preference': ride.talkative_preference,
            'pets_allowed': ride.pets_allowed,
            'air_conditioning': ride.air_conditioning,
            'children_allowed': ride.children_allowed
        } for ride in rides]
        
        return jsonify({'status': 'success', 'rides': rides_data}), 200
    
    except Exception as e:
        logger.error(f"Error fetching rides: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to retrieve rides.'}), 500


@app.route('/rides/<int:ride_id>', methods=['GET'])
def get_ride(ride_id):
    """Fetch a specific ride."""
    
    try:
        ride = Ride.query.get(ride_id)
        
        if not ride:
            return jsonify({'status': 'error', 'message': 'Ride not found.'}), 404
        
        ride_data = {
            'id': ride.id,
            'creator_id': ride.creator_id,
            'destination': ride.destination,
            'destination_coordinates': ride.destination_coordinates,
            'departure_time': ride.departure_time.isoformat(),
            'trip_type': ride.trip_type,
            'return_time': ride.return_time.isoformat() if ride.return_time else None,
            'return_destination': ride.return_destination,
            'return_destination_coordinates': ride.return_destination_coordinates,
            'preferred_gender': ride.preferred_gender,
            'preferred_music': ride.preferred_music,
            'smoking_preference': ride.smoking_preference,
            'talkative_preference': ride.talkative_preference,
            'pets_allowed': ride.pets_allowed,
            'air_conditioning': ride.air_conditioning,
            'children_allowed': ride.children_allowed
        }
        
        return jsonify({'status': 'success', 'ride': ride_data}), 200
    
    except Exception as e:
        logger.error(f"Error fetching ride: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to retrieve ride.'}), 500


@app.route('/', methods=['GET', 'POST'])
def index():
    """Handle satisfaction form submission."""
    
    if request.method == 'POST':
        # Get form data
        rating = request.form.get('rating')  # Rating is optional
        comments = request.form.get('comments')  # Comments are optional
        
        # Create a new Satisfaction object with optional fields
        satisfaction_entry = Satisfaction(rating=rating if rating else None, comments=comments if comments else None)
        
        # Add the new entry to the session and commit to the database
        db.session.add(satisfaction_entry)
        db.session.commit()
        
        # Redirect or send a success message
        return redirect(url_for('index'))  # You can redirect to a success page or show a message
    
    return render_template('index.html')  # Ensure index.html has the form as part of it


@app.route('/matching')
def matching():
    """Match passengers with available rides."""
    
    # Get the most recent passenger search
    current_passenger = Passenger.query.filter_by(creator_id=session['user_id']).order_by(Passenger.created_at.desc()).first()
    
    if not current_passenger:
        flash('No search criteria found. Please search for a ride first.')
        return redirect(url_for('search_ride'))
    
    # Query available rides based on matching criteria
    matching_rides = Ride.query.filter(
        Ride.destination == current_passenger.destination,
        Ride.departure_time >= current_passenger.departure_time - timedelta(hours=2),
        Ride.departure_time <= current_passenger.departure_time + timedelta(hours=2),
        Ride.Finished == False,  # Ensure that Finished is False
        Ride.creator_id != current_passenger.creator_id  # Exclude the current user's own rides
    )
    
    # Apply additional filters based on preferences
    if current_passenger.preferred_gender != 'any':
        matching_rides = matching_rides.filter(Ride.preferred_gender.in_(['any', current_passenger.preferred_gender]))
    if current_passenger.smoking_preference != 'any':
        matching_rides = matching_rides.filter(Ride.smoking_preference == current_passenger.smoking_preference)
    if current_passenger.pets_allowed != 'any':
        matching_rides = matching_rides.filter(Ride.pets_allowed == current_passenger.pets_allowed)
    if current_passenger.children_allowed != 'any':
        matching_rides = matching_rides.filter(Ride.children_allowed == current_passenger.children_allowed)
    if current_passenger.trip_type == 'two-way' and current_passenger.return_time:
        matching_rides = matching_rides.filter(
            Ride.trip_type == 'two-way',
            Ride.return_destination == current_passenger.return_destination,
            Ride.return_time == current_passenger.return_time - timedelta(hours=2),
            Ride.return_time <= current_passenger.return_time + timedelta(hours=2)
        )
    
    # Execute the query
    matching_rides = matching_rides.all()
    
    # Get driver information for each ride
    rides_with_drivers = []
    for ride in matching_rides:
        driver = User.query.get(ride.creator_id)
        rides_with_drivers.append({
            'ride': ride,
            'driver': driver
        })
    
    return render_template(
        'matching.html',
        matches=rides_with_drivers,
        search_criteria=current_passenger,
    )


if __name__ == '__main__':
    with app.app_context():
        # Ensure database is initialized
        db.create_all()
    
    app.run(debug=True, port=5001)



