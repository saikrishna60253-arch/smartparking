import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "smart_parking_secret_key")

# Database Configuration (supports MySQL via PyMySQL, or SQLite fallback for Vercel/local)
MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "sai@60253")
MYSQL_DB = os.environ.get("MYSQL_DB", "smart_parking")

USE_MYSQL = False

try:
    import pymysql
    pymysql.install_as_MySQLdb()
    # Test connection if environment explicitly specifies remote MySQL or local connection
    connection = pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
        connect_timeout=3
    )
    connection.close()
    USE_MYSQL = True
except Exception:
    USE_MYSQL = False


def get_db():
    if USE_MYSQL:
        import pymysql
        conn = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            autocommit=True,
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn, conn.cursor()
    else:
        conn = sqlite3.connect("/tmp/smart_parking.db" if os.path.exists("/tmp") else "smart_parking.db")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        # Initialize SQLite tables if not exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                slot_id INTEGER,
                vehicle_number TEXT,
                booking_date TEXT,
                booking_time TEXT
            )
        """)
        conn.commit()
        return conn, cur


# -----------------------------
# Home Page
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")


# -----------------------------
# Register
# -----------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        try:
            conn, cur = get_db()
            if USE_MYSQL:
                cur.execute(
                    "INSERT INTO users(name,email,password) VALUES(%s,%s,%s)",
                    (name, email, password),
                )
            else:
                cur.execute(
                    "INSERT INTO users(name,email,password) VALUES(?,?,?)",
                    (name, email, password),
                )
                conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except Exception as e:
            return f"Registration Error: {str(e)}", 400

    return render_template("register.html")


# -----------------------------
# Login
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        try:
            conn, cur = get_db()
            if USE_MYSQL:
                cur.execute(
                    "SELECT * FROM users WHERE email=%s AND password=%s",
                    (email, password),
                )
            else:
                cur.execute(
                    "SELECT * FROM users WHERE email=? AND password=?",
                    (email, password),
                )
            user = cur.fetchone()
            conn.close()

            if user:
                return redirect(url_for("dashboard"))
            else:
                return "Invalid Email or Password"
        except Exception as e:
            return f"Login Error: {str(e)}", 500

    return render_template("login.html")


# -----------------------------
# Dashboard
# -----------------------------
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# -----------------------------
# Booking
# -----------------------------
@app.route("/booking", methods=["GET", "POST"])
def booking():
    if request.method == "POST":
        vehicle_number = request.form["vehicle_number"]
        slot_id = int(request.form["slot"])
        booking_date = request.form["booking_date"]
        booking_time = request.form["booking_time"]

        try:
            conn, cur = get_db()
            # Check whether slot is already booked
            if USE_MYSQL:
                cur.execute(
                    "SELECT * FROM bookings WHERE slot_id=%s AND booking_date=%s",
                    (slot_id, booking_date),
                )
            else:
                cur.execute(
                    "SELECT * FROM bookings WHERE slot_id=? AND booking_date=?",
                    (slot_id, booking_date),
                )

            existing_booking = cur.fetchone()

            if existing_booking:
                conn.close()
                return render_template(
                    "booking.html",
                    message="This parking slot is already booked!"
                )

            user_id = 1

            if USE_MYSQL:
                cur.execute(
                    "INSERT INTO bookings (user_id, slot_id, vehicle_number, booking_date, booking_time) VALUES (%s,%s,%s,%s,%s)",
                    (user_id, slot_id, vehicle_number, booking_date, booking_time),
                )
            else:
                cur.execute(
                    "INSERT INTO bookings (user_id, slot_id, vehicle_number, booking_date, booking_time) VALUES (?,?,?,?,?)",
                    (user_id, slot_id, vehicle_number, booking_date, booking_time),
                )
                conn.commit()

            conn.close()
            return render_template("booking.html", message="Booking Successful!")
        except Exception as e:
            return f"Booking Error: {str(e)}", 500

    return render_template("booking.html")


# -----------------------------
# View Bookings
# -----------------------------
@app.route("/view_bookings")
def view_bookings():
    try:
        conn, cur = get_db()
        cur.execute(
            """
            SELECT booking_id, vehicle_number, slot_id, booking_date, booking_time
            FROM bookings ORDER BY booking_id DESC
            """
        )
        bookings = cur.fetchall()
        conn.close()
        return render_template("view_bookings.html", bookings=bookings)
    except Exception as e:
        return f"View Bookings Error: {str(e)}", 500


# -----------------------------
# Logout
# -----------------------------
@app.route("/logout")
def logout():
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)