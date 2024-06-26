from flask import Flask, render_template, request, redirect, url_for
import random
from threading import Semaphore
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = 'your_secret_key'  

MAX_DAYS = 7
MAX_NAME_LENGTH = 50
MAX_SUBJECT_LENGTH = 50
MAX_DIVISIONS = 5

# User class for authentication
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

# Login manager configuration
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Define a user for admin login (replace with database or other authentication methods)
users = {1: User(1, 'admin', 'kle@123')}  # Replace password with a strong one

@login_manager.user_loader
def load_user(user_id):
    return users.get(int(user_id))

# Helper function to find user by username
def get_user_by_username(username):
    for user in users.values():
        if user.username == username:
            return user
    return None

# Class definitions
class Class:
    def __init__(self, name, time, faculty, subject, division, classroom):
        self.name = name
        self.time = time
        self.faculty = faculty
        self.subject = subject
        self.division = division
        self.classroom = classroom

class Timetable:
    def __init__(self):
        self.classes = [[] for _ in range(MAX_DAYS)]
        self.num_classes = [0] * MAX_DAYS

class Subject:
    def __init__(self, name, faculty):
        self.name = name
        self.faculty = faculty

# Function to generate class name
def generate_class_name(subject, faculty, division):
    return f"{subject.name}_{faculty}_{division}"

# Round robin scheduling function
def round_robin_scheduling(professors, subjects, divisions, time_quantum):
    timetables = {}
    classrooms = {}  # Dictionary to store classrooms for each division
    faculty_semaphores = {faculty: Semaphore(value=1) for faculty in professors}

    # Ask for classrooms for each division
    for division in range(1, divisions + 1):
        classroom = input(f"Enter the classroom for Division {division}: ")
        classrooms[division] = classroom

    # Define time slots for each day, excluding break times
    time_slots = [
        # Sunday (Holiday)
        [],
        # Monday to Saturday (excluding break times)
        ["8:00 AM", "9:00 AM", "10:00 AM", "11:15 AM", "12:15 PM", "1:15 ", "2:00 PM"],
        ["8:00 AM", "9:00 AM", "10:00 AM", "11:15 AM", "12:15 PM", "1:15 ", "2:00 PM"],
        ["8:00 AM", "9:00 AM", "10:00 AM", "11:15 AM", "12:15 PM", "1:15 ", "2:00 PM"],
        ["8:00 AM", "9:00 AM", "10:00 AM", "11:15 AM", "12:15 PM", "1:15 ", "2:00 PM"],
        ["8:00 AM", "9:00 AM", "10:00 AM", "11:15 AM", "12:15 PM", "1:15 ", "2:00 PM"],
        ["8:00 AM", "9:00 AM", "10:00 AM", "11:15 AM", "12:15 PM"]  # Half Day (Saturday)
    ]

    # Initialize counters for each faculty member
    faculty_counters = {faculty_name: 0 for faculty_name in professors}

    for division in range(1, divisions + 1):
        timetable = Timetable()
        timetables[division] = timetable

    for day in range(MAX_DAYS):
        if day == 0:  # Sunday (Holiday)
            continue
        for time_slot in range(len(time_slots[day])):
            for division in range(1, divisions + 1):
                # Randomly select a faculty member from the list of professors
                faculty_name = random.choice(professors)
                if not faculty_semaphores[faculty_name].acquire(blocking=False):
                    continue  # Skip this faculty if already assigned a class

                # Randomly select a subject from the list associated with the faculty
                subject = random.choice(subjects[faculty_name])

                # Generate a unique class name
                class_name = generate_class_name(subject, faculty_name, division)

                # Check if any other division has the same class at the same time
                conflict = False
                for other_division, other_timetable in timetables.items():
                    if other_division != division:
                        for other_class in other_timetable.classes[day]:
                            if other_class.time == time_slots[day][time_slot] and other_class.subject == subject.name:
                                conflict = True
                                break
                if conflict:
          # Do not release semaphore if conflict
                    continue  # Skip this faculty and move on to the next

        # ... rest of the code for creating class and adding it to timetable ...

                faculty_semaphores[faculty_name].release()

                # Create the class and add it to the timetable
                class_ = Class(class_name, time_slots[day][time_slot], faculty_name, subject.name, division, classrooms[division])
                timetables[division].classes[day].append(class_)
                timetables[division].num_classes[day] += 1

                # Increment the counter for the assigned faculty member
                faculty_counters[faculty_name] += 1
                faculty_semaphores[faculty_name].release()  # Release semaphore after assignme

    return timetables

# Function to print timetable in HTML format
def print_timetable_html(timetables):
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    time_slots = ["8:00 AM", "9:00 AM", "10:00 AM", "11:15 AM", "12:15 PM", "1:15 PM", "2:00 PM"]

    timetable_html = ""
    for division, timetable in timetables.items():
        timetable_html += f"<h2>Timetable for Division {division} (Classroom: {timetable.classes[1][0].classroom})</h2>"
        timetable_html += "<table border='1' style='border-collapse: collapse; width: 100%;'>"
        
        # Header Row
        timetable_html += "<tr><th>Time</th>"
        for day in days_of_week:
            timetable_html += f"<th>{day}</th>"
        timetable_html += "</tr>"

        # Time Slot Rows
        for time in time_slots:
            # Insert breaks as rows
            if time == "11:15 AM":
                timetable_html += f"<tr><td colspan='{len(days_of_week) + 1}' style='text-align: center;'>Breakfast Break(11:00-11:15)</td></tr>"

            if time == "1:15 PM":  # New condition for lunch break
                timetable_html += f"<tr><td colspan='{len(days_of_week) + 1}' style='text-align: center;'>Lunch Break(1:15-2:00)</td></tr>"

            timetable_html += f"<tr><td>{time}</td>"
            for day in range(1, MAX_DAYS):
                if day == 0:  # Skip Sunday (Holiday)
                    continue
                cell_content = ""
                for class_ in timetable.classes[day]:
                    if class_.time == time:
                        cell_content = f"{class_.name} ({class_.faculty})"
                        break
                timetable_html += f"<td>{cell_content}</td>"
            timetable_html += "</tr>"

        timetable_html += "</table>"
    return timetable_html

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = get_user_by_username(username)
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('input_form'))  # Redirect to input form after successful login
        else:
            return render_template("login.html", error="Invalid username or password")
    else:
        return render_template("login.html")

# Route for displaying the input form
@app.route("/input_form")
@login_required
def input_form():
    return render_template("input_form.html")

# Route for handling form submission and generating timetable
@app.route("/generate", methods=["POST"])
@login_required
def generate_timetable():
    num_faculty = int(request.form["num_faculty"])
    professors = []
    subjects = {}
    for i in range(num_faculty):
        professor_name = request.form[f"faculty_{i + 1}_name"]
        professors.append(professor_name)
        subjects[professor_name] = []
        num_subjects = int(request.form[f"faculty_{i + 1}_subjects"])
        for j in range(num_subjects):
            subject_name = request.form[f"faculty_{i + 1}_subject_{j + 1}"]
            subjects[professor_name].append(Subject(subject_name, professor_name))

    divisions = int(request.form["divisions"])
    time_quantum = int(request.form["time_quantum"])

    timetables = round_robin_scheduling(professors, subjects, divisions, time_quantum)

    timetable_html = print_timetable_html(timetables)
    return render_template("timetable.html", timetable_html=timetable_html)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)
