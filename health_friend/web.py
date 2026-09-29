from flask import Flask, render_template, request, redirect, flash, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from .recommendations import preprocess_state, generate_recommendations, update_q_table
from .recommendations import data, POLICY_VERSION
import os
import secrets
import math
from functools import wraps
from pathlib import Path
from .simulation.views import blueprint as simulation_blueprint
from .prediction import blueprint as prediction_blueprint


PROJECT_ROOT = Path(__file__).resolve().parents[1]
app = Flask(__name__, instance_path=str(PROJECT_ROOT / 'instance'))
Path(app.instance_path).mkdir(parents=True, exist_ok=True)
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.register_blueprint(simulation_blueprint)
app.register_blueprint(prediction_blueprint)

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///users.db')
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
    # Preserve the incompatible legacy questionnaire table.
    __tablename__ = 'health_questionnaire'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
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
            session.clear()
            session['username'] = user.username
            session['user_id'] = user.id  # Store the user's ID in the session
            flash('Login successful!', 'success')
            return redirect(url_for('questionnaire'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html')

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session or db.session.get(User, session['user_id']) is None:
            session.clear()
            flash('Please log in first.', 'warning')
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapped


@app.route('/questionnaire', methods=['GET', 'POST'])
@login_required
def questionnaire():
    if request.method == 'POST':
        try:
            values = {}
            bounds = {
                'age': (int, 18, 100), 'sleep_duration': (float, 4, 10),
                'quality_of_sleep': (int, 1, 10),
                'physical_activity_level': (int, 1, 100),
                'stress_level': (int, 1, 10), 'heart_rate': (int, 40, 200),
                'daily_steps': (int, 1000, 20000),
            }
            for key, (cast, low, high) in bounds.items():
                value = cast(request.form.get(key, ''))
                if not math.isfinite(value) or not low <= value <= high:
                    raise ValueError(key)
                values[key] = value
            for key in ('gender', 'occupation', 'bmi_category', 'blood_pressure'):
                values[key] = request.form.get(key, '').strip()
                if not values[key]:
                    raise ValueError(key)
            if values['gender'] not in ('Male', 'Female') or values['bmi_category'] not in ('Underweight', 'Normal', 'Overweight', 'Obese'):
                raise ValueError('Invalid selection')
            values['sleep_disorder'] = request.form.get('sleep_disorder') or 'None'
        except (ValueError, TypeError):
            return render_template('questionnaire.html', error='Please complete all fields with valid values.'), 400
        db.session.add(Questionnaire(user_id=session['user_id'], **values))
        db.session.commit()
        session.pop('recommendation_context', None)
        return redirect(url_for('thank_you'))
    return render_template('questionnaire.html')


@app.route('/feedback', methods=['POST'])
@login_required
def feedback():
    context = session.get('recommendation_context')
    if not context:
        flash('No recommendations to provide feedback on.', 'error')
        return redirect(url_for('questionnaire'))
    rewards = {}
    for category, actions in context['actions'].items():
        for index, action in enumerate(actions):
            scores = request.form.getlist(f'feedback[{category}][{index}]')
            if len(scores) != 1 or scores[0] not in ('1', '-1'):
                return 'Please rate every recommendation as useful or not useful.', 400
            rewards.setdefault(action, []).append(int(scores[0]))
    state = tuple(context['state'])
    for action, scores in rewards.items():
        update_q_table(state, int(action), sum(scores) / len(scores), state)
    session.pop('recommendation_context', None)
    flash('Thank you for your feedback!', 'success')
    return redirect(url_for('home'))


@app.route('/your-data')
@login_required
def your_data():
    records = Questionnaire.query.filter_by(user_id=session['user_id']).order_by(Questionnaire.id.desc()).all()
    return render_template('view_data.html', data=records)


@app.route('/thank-you')
@login_required
def thank_you():
    latest = Questionnaire.query.filter_by(user_id=session['user_id']).order_by(Questionnaire.id.desc()).first()
    if latest is None:
        flash('Please complete the questionnaire first.', 'warning')
        return redirect(url_for('questionnaire'))
    context = session.get('recommendation_context')
    if not context or context.get('policy_version') != POLICY_VERSION or context['questionnaire_id'] != latest.id:
        user_data = {'Age': latest.age, 'Gender': latest.gender,
                     'BMI Category': latest.bmi_category,
                     'Stress Level': latest.stress_level,
                     'Sleep Duration': latest.sleep_duration}
        recommendations, actions = generate_recommendations(user_data, return_actions=True)
        context = {'questionnaire_id': latest.id, 'policy_version': POLICY_VERSION,
                   'state': list(preprocess_state(user_data)), 'actions': actions}
        session['recommendation_context'] = context
    recommendations = {
        category: [str(data.iloc[action][category]) for action in actions]
        for category, actions in context['actions'].items()
    }
    return render_template('thank_you.html', recommendations=recommendations)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

