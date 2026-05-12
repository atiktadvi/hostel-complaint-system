
from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

# DATABASE SETUP
conn = sqlite3.connect("hostel.db")
cursor = conn.cursor()

# USERS TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    password TEXT,
    room TEXT
)
""")

# COMPLAINTS TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS complaints(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    complaint_type TEXT,
    description TEXT,
    status TEXT DEFAULT 'Pending'
)
""")

# ADMIN TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS admin(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT,
    password TEXT
)
""")

# DEFAULT ADMIN
cursor.execute("""
INSERT OR IGNORE INTO admin(id,email,password)
VALUES(1,'admin@gmail.com','admin123')
""")

conn.commit()
conn.close()


# HOME
@app.route('/')
def home():
    return redirect('/login')


# REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():

    success = None
    error = None

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        room = request.form['room']

        conn = sqlite3.connect("hostel.db")
        cursor = conn.cursor()

        # CHECK EXISTING EMAIL
        cursor.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:

            error = "Email already exists"

        else:

            cursor.execute(
                "INSERT INTO users(name,email,password,room) VALUES(?,?,?,?)",
                (name, email, password, room)
            )

            conn.commit()

            success = "Registration Successful"

        conn.close()

    return render_template(
        "register.html",
        success=success,
        error=error
    )


# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():

    error = None

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect("hostel.db")
        cursor = conn.cursor()

        # ADMIN LOGIN
        cursor.execute(
            "SELECT * FROM admin WHERE email=? AND password=?",
            (email, password)
        )

        admin = cursor.fetchone()

        if admin:

            session['admin'] = True

            return redirect('/admin')

        # USER LOGIN
        cursor.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        )

        user = cursor.fetchone()

        conn.close()

        if user:

            session['user_id'] = user[0]
            session['name'] = user[1]

            return redirect('/dashboard')

        else:

            error = "Invalid Email or Password"

    return render_template(
        "login.html",
        error=error
    )

# DASHBOARD
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():

    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect("hostel.db")
    cursor = conn.cursor()

    # ADD COMPLAINT
    if request.method == 'POST':

        complaint_type = request.form['type']
        description = request.form['description']

        cursor.execute(
            "INSERT INTO complaints(user_id, complaint_type, description) VALUES(?,?,?)",
            (session['user_id'], complaint_type, description)
        )

        conn.commit()

    # FETCH COMPLAINTS
    cursor.execute(
        "SELECT * FROM complaints WHERE user_id=? ORDER BY id DESC",
        (session['user_id'],)
    )

    complaints = cursor.fetchall()

    # TOTAL
    total_complaints = len(complaints)

    # PENDING
    cursor.execute(
        "SELECT COUNT(*) FROM complaints WHERE user_id=? AND status='Pending'",
        (session['user_id'],)
    )

    pending_count = cursor.fetchone()[0]

    # RESOLVED
    cursor.execute(
        "SELECT COUNT(*) FROM complaints WHERE user_id=? AND status='Resolved'",
        (session['user_id'],)
    )

    resolved_count = cursor.fetchone()[0]

    # RECENT ACTIVITY
    recent_activity = "No recent activity"

    if total_complaints > 0:
        recent_activity = "You recently submitted a complaint"

    conn.close()

    return render_template(
        "dashboard.html",
        complaints=complaints,
        name=session['name'],
        total_complaints=total_complaints,
        pending_count=pending_count,
        resolved_count=resolved_count,
        recent_activity=recent_activity
    )


# ADMIN PANEL
@app.route('/admin', methods=['GET', 'POST'])
def admin():

    if 'admin' not in session:
        return redirect('/login')

    conn = sqlite3.connect("hostel.db")
    cursor = conn.cursor()

    # UPDATE STATUS
    if request.method == 'POST':

        complaint_id = request.form['complaint_id']
        new_status = request.form['status']

        cursor.execute(
            "UPDATE complaints SET status=? WHERE id=?",
            (new_status, complaint_id)
        )

        conn.commit()

    cursor.execute("""
    SELECT complaints.id,
           users.name,
           users.room,
           complaints.complaint_type,
           complaints.description,
           complaints.status
    FROM complaints
    JOIN users
    ON complaints.user_id = users.id
    ORDER BY complaints.id DESC
    """)

    complaints = cursor.fetchall()

    conn.close()

    return render_template(
        "admin.html",
        complaints=complaints
    )


# LOGOUT
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/login')


# RUN
if __name__ == '__main__':
    app.run(debug=True)
