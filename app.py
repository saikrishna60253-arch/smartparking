from flask import Flask, render_template, request, redirect, url_for
from flask_mysqldb import MySQL

app = Flask(__name__)

# -----------------------------
# MySQL Configuration
# -----------------------------
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "sai@60253"
app.config["MYSQL_DB"] = "smart_parking"

mysql = MySQL(app)

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

        cur = mysql.connection.cursor()

        cur.execute(
            """
            INSERT INTO users(name,email,password)
            VALUES(%s,%s,%s)
            """,
            (name, email, password),
        )

        mysql.connection.commit()
        cur.close()

        return redirect(url_for("login"))

    return render_template("register.html")


# -----------------------------
# Login
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        cur = mysql.connection.cursor()

        cur.execute(
            """
            SELECT * FROM users
            WHERE email=%s AND password=%s
            """,
            (email, password),
        )

        user = cur.fetchone()

        cur.close()

        if user:
            return redirect(url_for("dashboard"))
        else:
            return "Invalid Email or Password"

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

        cur = mysql.connection.cursor()

        # Check whether slot is already booked
        cur.execute(
            """
            SELECT * FROM bookings
            WHERE slot_id=%s AND booking_date=%s
            """,
            (slot_id, booking_date),
        )

        existing_booking = cur.fetchone()

        if existing_booking:
            cur.close()
            return render_template(
                "booking.html",
                message="This parking slot is already booked!"
            )

        # Dummy logged-in user
        user_id = 1

        # Insert booking
        cur.execute(
            """
            INSERT INTO bookings
            (user_id, slot_id, vehicle_number, booking_date, booking_time)
            VALUES (%s,%s,%s,%s,%s)
            """,
            (
                user_id,
                slot_id,
                vehicle_number,
                booking_date,
                booking_time,
            ),
        )

        mysql.connection.commit()
        cur.close()

        return render_template(
            "booking.html",
            message="Booking Successful!"
        )

    return render_template("booking.html")


# -----------------------------
# View Bookings
# -----------------------------
@app.route("/view_bookings")
def view_bookings():

    cur = mysql.connection.cursor()

    cur.execute(
        """
        SELECT booking_id,
               vehicle_number,
               slot_id,
               booking_date,
               booking_time
        FROM bookings
        ORDER BY booking_id DESC
        """
    )

    bookings = cur.fetchall()

    cur.close()

    return render_template(
        "view_bookings.html",
        bookings=bookings
    )


# -----------------------------
# Logout
# -----------------------------
@app.route("/logout")
def logout():
    return redirect(url_for("home"))


# -----------------------------
# Run App
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)