from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
import bcrypt
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import json

# Initialize the Flask app with static and template folders specified
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)  # Enable CORS for all domains
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Flask-Login and Flask-SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect to login if not authenticated

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client['chat_app']
user_collection = db['users']
chats_collection = db['chats']

# Define User model
class User(UserMixin):
    def __init__(self, username):
        self.username = username

    def get_id(self):
        return self.username

@login_manager.user_loader
def load_user(username):
    user = user_collection.find_one({"username": username})
    return User(username=user["username"]) if user else None

# Custom JSON Encoder to handle ObjectId serialization
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

app.json_encoder = CustomJSONEncoder

# User registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if the username already exists
        if user_collection.find_one({"username": username}):
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('register'))
        
        # Hash the password and save the user
        password_hash = generate_password_hash(password)
        user_collection.insert_one({"username": username, "password": password_hash})
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# User login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_data = user_collection.find_one({"username": username})
        
        if user_data and check_password_hash(user_data['password'], password):
            user = User(username=user_data['username'])
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('chat'))
        else:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
    
    return render_template('login.html')

# User logout route
@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Add contact route
@app.route('/add_contact', methods=['POST'])
@login_required
def add_contact():
    data = request.get_json()
    contact_username = data.get("contact_username")
    user = current_user.get_id()
    
    # Add contact to the user's contacts list
    user_collection.update_one(
        {"username": user},
        {"$addToSet": {"contacts": contact_username}}
    )
    return jsonify({"message": f"{contact_username} added to contacts"})

# Get all users route (fixed list of names)
@app.route('/users')
@login_required
def get_users():
    # Return a fixed list of usernames
    user_list = ["Jeet Kumar Gupta", "Prabin Dhrua", "Dhruv Dewangan", "Satyam Kumar Mehta"]
    return jsonify(user_list)

# Socket.IO message handling
@socketio.on('message')
def handle_message(data):
    if not current_user.is_authenticated:
        return  # Ensure user is logged in before proceeding
    
    username = current_user.get_id()
    message = data.get("message")
    chat_data = {"username": username, "message": message, "type": "text"}
    
    # Save chat message to MongoDB
    chats_collection.insert_one(chat_data)
    emit('message', chat_data, broadcast=True)

# Socket.IO file handling
@socketio.on('file')
def handle_file(data):
    if not current_user.is_authenticated:
        return  # Ensure user is logged in before proceeding
    
    username = current_user.get_id()
    file_data = data.get("data")
    filename = secure_filename(data.get("filename"))
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # Save file to the upload folder
    try:
        with open(filepath, "wb") as file:
            file.write(file_data)

        chat_data = {"username": username, "message": f"File sent: {filename}", "type": "file", "filepath": filepath}
        
        # Save chat data to MongoDB and broadcast the file message
        chats_collection.insert_one(chat_data)
        emit('message', chat_data, broadcast=True)
    except Exception as e:
        print(f"Error saving file: {e}")
        emit('error', {'message': 'Failed to upload file'})

# Chat room route (protected)
@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html')  # Ensure 'chat.html' exists in 'templates'

# Home route (redirects to chat)
@app.route('/')
def home():
    return redirect(url_for('chat'))

# Favicon route
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    socketio.run(app, debug=True)
