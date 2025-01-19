from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import sqlite3

app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)

# Initialize database
def init_db():
    conn = sqlite3.connect("employee_management.db")
    cursor = conn.cursor()
    # Create admin table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    # Create employees table with employee_id as unique identifier
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            employee_id INTEGER UNIQUE NOT NULL,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            department TEXT NOT NULL,
            position TEXT NOT NULL,
            salary REAL NOT NULL,
            PRIMARY KEY (employee_id)
        )
    """)
    # Insert default admin if not exists
    cursor.execute("SELECT * FROM admin WHERE username = ?", ("admin",))
    if cursor.fetchone() is None:
        hashed_password = bcrypt.generate_password_hash("admin123").decode("utf-8")
        cursor.execute("INSERT INTO admin (username, password) VALUES (?, ?)", ("admin", hashed_password))
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    conn = sqlite3.connect("employee_management.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admin WHERE username = ?", (data["username"],))
    admin = cursor.fetchone()
    conn.close()
    if admin and bcrypt.check_password_hash(admin[2], data["password"]):
        return jsonify({"message": "Login successful!"}), 200
    else:
        return jsonify({"message": "Invalid username or password!"}), 401

@app.route('/employees', methods=['GET'])
def get_employees():
    conn = sqlite3.connect("employee_management.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees")
    employees = cursor.fetchall()
    conn.close()
    return jsonify([dict(zip([column[0] for column in cursor.description], emp)) for emp in employees])

@app.route('/add_employee', methods=['POST'])
def add_employee():
    data = request.json
    conn = sqlite3.connect("employee_management.db")
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO employees (employee_id, name, age, department, position, salary)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (data["employee_id"], data["name"], data["age"], data["department"], data["position"], data["salary"]))
        conn.commit()
        conn.close()
        return jsonify({"message": "Employee added successfully!"}), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"message": "Employee ID already exists!"}), 400

@app.route('/update_employee/<int:employee_id>', methods=['PUT'])
def update_employee(employee_id):
    data = request.json
    conn = sqlite3.connect("employee_management.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE employees
        SET name = ?, age = ?, department = ?, position = ?, salary = ?
        WHERE employee_id = ?
    """, (data["name"], data["age"], data["department"], data["position"], data["salary"], employee_id))
    conn.commit()
    conn.close()
    return jsonify({"message": "Employee updated successfully!"}), 200

@app.route('/delete_employee/<int:employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    conn = sqlite3.connect("employee_management.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM employees WHERE employee_id = ?", (employee_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Employee deleted successfully!"}), 200

@app.route('/logout', methods=['POST'])
def logout():
    return redirect(url_for('login_page'))

if __name__ == "__main__":
    app.run(debug=True)
