from flask import Flask, render_template, request, redirect, flash, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from bbl3 import preprocess_state, choose_action, generate_recommendations, update_q_table
from bbl3 import data, recommendation_columns
import random 
current_state = None







app = Flask(__name__, template_folder='../templates')
app.secret_key = 'your_secret_key'

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)

# Questionnaire Model
class Questionnaire(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    gender = db.Column(db.String(10), nullable=False)  # Assurez-vous que cette ligne existe
    age = db.Column(db.Integer, nullable=False)
    occupation = db.Column(db.String(255), nullable=False)
    sleep_duration = db.Column(db.Float, nullable=False)
    quality_of_sleep = db.Column(db.Integer, nullable=False)
    physical_activity_level = db.Column(db.Integer, nullable=False)
    stress_level = db.Column(db.Integer, nullable=False)
    bmi_category = db.Column(db.String(50), nullable=False)
    blood_pressure = db.Column(db.String(20), nullable=False)
    heart_rate = db.Column(db.Integer, nullable=False)
    daily_steps = db.Column(db.Integer, nullable=False)
    sleep_disorder = db.Column(db.String(255), nullable=True)


# Initialize the database
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Hash the password
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Check if user already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already taken. Please choose another.', 'warning')
            return redirect(url_for('signup'))

        # Save the new user to the database
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Signup successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Find the user in the database
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['username'] = user.username
            session['user_id'] = user.id  # Store the user's ID in the session
            flash('Login successful!', 'success')
            return redirect(url_for('questionnaire'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/questionnaire', methods=['GET', 'POST'])
def questionnaire():
    global current_state  # Use the global variable
    if request.method == 'POST':
        user_input = {
            "Age": int(request.form['age']),
            "Gender": request.form['gender'],
            "BMI Category": request.form['bmi_category'],
            "Stress Level": int(request.form['stress_level']),
            "Sleep Duration": float(request.form['sleep_duration']),
        }

        current_state = preprocess_state(user_input)  # Set current_state
        recommendations = generate_recommendations(user_input)
        return render_template('thank_you.html', recommendations=recommendations)

    return render_template('questionnaire.html')

@app.route('/feedback', methods=['POST'])
def feedback():
    global current_state
    if not current_state:
        flash("No recommendations to provide feedback on.", "error")
        return redirect(url_for('questionnaire'))

    feedback = request.form.to_dict(flat=False)  # Extract feedback for each recommendation

    # Process feedback for each recommendation
    for category, scores in feedback.items():
        for index, score in enumerate(scores):  # Iterate over recommendations in each category
            reward = int(score)
            action_index = random.choice(range(len(data)))  # Choose a random action index (replace with logic if needed)
            next_state = current_state  # Simulate next state (adjust if needed)

            # Update Q-table with feedback
            update_q_table(current_state, action_index, reward, next_state)

    flash("Thank you for your feedback!", "success")
    return redirect(url_for('home'))


@app.route('/your-data')
def your_data():
    data = Questionnaire.query.all()  # Fetch all rows
    return render_template('view_data.html', data=data)



@app.route('/thank-you')
def thank_you():
    if 'user_id' not in session:
        flash('You must log in to view this page.', 'warning')
        return redirect(url_for('login'))

    # Fetch the latest questionnaire data for the logged-in user
    user_id = session['user_id']
    latest_data = Questionnaire.query.filter_by(user_id=user_id).order_by(Questionnaire.id.desc()).first()

    # Prepare data for the RL agent
    user_data = {
        "Age": latest_data.age,
        "Gender": latest_data.gender,
        "BMI Category": latest_data.bmi_category,
        "Stress Level": latest_data.stress_level,
        "Sleep Duration": latest_data.sleep_duration,
    }

    # Convert user data to a state
    state = preprocess_state(user_data)

    # Generate recommendations
    action_index = choose_action(state)
    recommendations = data.iloc[action_index][recommendation_columns].to_dict()

    return render_template('thank_you.html', recommendations=recommendations)

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
