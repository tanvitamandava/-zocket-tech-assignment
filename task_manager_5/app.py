from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import speech_recognition as sr
import pyttsx3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///task_manager.db'
db = SQLAlchemy(app)

recognizer = sr.Recognizer()
engine = pyttsx3.init()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    done = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('tasks', lazy=True))

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('tasks'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash("Login successful!", "success")
            return redirect(url_for('tasks'))
        else:
            flash("Invalid credentials", "danger")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        if User.query.filter_by(username=username).first():
            flash("Username already exists", "danger")
            return redirect(url_for('register'))
        
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route('/tasks', methods=['GET', 'POST'])
def tasks():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        task_name = request.form['task_name']
        new_task = Task(name=task_name, user_id=session['user_id'])
        db.session.add(new_task)
        db.session.commit()
        flash("Task added successfully!", "success")
        return redirect(url_for('tasks'))

    tasks = Task.query.filter_by(user_id=session['user_id']).all()
    current_datetime = datetime.now().strftime("%d/%m/%Y %H:%M")  # Format: dd/mm/yyyy hh:mm
    return render_template('tasks.html', tasks=tasks, current_datetime=current_datetime)

@app.route('/tasks/edit/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)

    if request.method == 'POST':
        task.name = request.form['task_name']
        db.session.commit()
        flash("Task updated successfully!", "success")
        return redirect(url_for('tasks'))

    return render_template('edit_task.html', task=task)

@app.route('/tasks/mark_done/<int:task_id>')
def mark_done(task_id):
    task = Task.query.get_or_404(task_id)
    task.done = True
    db.session.commit()
    flash("Task marked as done!", "success")
    return redirect(url_for('tasks'))

@app.route('/tasks/delete/<int:task_id>')
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    flash("Task deleted!", "danger")
    return redirect(url_for('tasks'))

@app.route('/tasks/search', methods=['GET'])
def search():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    search_term = request.args.get('search_term')
    tasks = Task.query.filter(Task.name.contains(search_term), Task.user_id == session['user_id']).all()
    return render_template('search_results.html', tasks=tasks, searched=True)

@app.route('/voice-input', methods=['POST'])
def voice_input():
    with sr.Microphone() as source:
        flash("Listening for task input...", "info")
        audio = recognizer.listen(source)
        try:
            task_text = recognizer.recognize_google(audio)
            return jsonify({'task': task_text})
        except sr.UnknownValueError:
            return jsonify({'error': 'Could not understand the input'})
        except sr.RequestError:
            return jsonify({'error': 'Could not process the request'})

@app.route('/voice-output', methods=['POST'])
def voice_output():
    text = request.json.get('text', '')
    engine.say(text)
    engine.runAndWait()
    return jsonify({'message': 'Voice output played successfully'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
