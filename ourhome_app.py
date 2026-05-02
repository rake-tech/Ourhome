import os
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from functools import wraps

import requests
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_bcrypt import Bcrypt
from sqlalchemy import func, text
from werkzeug.utils import secure_filename

from config import Config
from models import Booking, Case, Donation, User, db
from flask import Flask, render_template
app = Flask(__name__)
@app.route("/")
def home():
    return render_template("login.html")  # or dashboard.html

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
bcrypt = Bcrypt(app)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
ORPHANAGES = [
    {"name": "Asha Child Care", "city": "Mumbai", "location": "Andheri East", "contact": "+91 98765 11111"},
    {"name": "Hope Harbor Home", "city": "Delhi", "location": "Lajpat Nagar", "contact": "+91 98765 22222"},
    {"name": "Udaya Foundation", "city": "Bengaluru", "location": "Whitefield", "contact": "+91 98765 33333"},
    {"name": "Nava Jeevan Home", "city": "Chennai", "location": "Adyar", "contact": "+91 98765 44444"},
    {"name": "Little Steps Trust", "city": "Hyderabad", "location": "Madhapur", "contact": "+91 98765 55555"},
]


def initialize_database():
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    db.create_all()
    if not app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite"):
        return

    columns = {
        "user": {
            "name": "VARCHAR(120)",
            "mobile": "VARCHAR(20)",
            "location": "VARCHAR(140)",
            "role": "VARCHAR(30)",
            "reset_token": "VARCHAR(120)",
            "reset_expires_at": "DATETIME",
            "created_at": "DATETIME",
        },
        "case": {"priority": "VARCHAR(20)", "created_at": "DATETIME"},
        "booking": {"location": "VARCHAR(140)", "notes": "VARCHAR(255)", "created_at": "DATETIME"},
        "donation": {"purpose": "VARCHAR(80)", "created_at": "DATETIME"},
    }

    with db.engine.begin() as connection:
        for table_name, table_columns in columns.items():
            quoted = f'"{table_name}"'
            existing = {row[1] for row in connection.execute(text(f"PRAGMA table_info({quoted})"))}
            for column_name, column_type in table_columns.items():
                if column_name not in existing:
                    connection.execute(text(f"ALTER TABLE {quoted} ADD COLUMN {column_name} {column_type}"))

        connection.execute(text('UPDATE "user" SET role = \'volunteer\' WHERE role IS NULL'))
        connection.execute(text('UPDATE "user" SET name = email WHERE name IS NULL OR name = \'\''))
        connection.execute(text('UPDATE "user" SET mobile = \'Not added\' WHERE mobile IS NULL OR mobile = \'\''))
        connection.execute(text('UPDATE "user" SET location = \'India\' WHERE location IS NULL OR location = \'\''))
        connection.execute(text('UPDATE "case" SET priority = \'medium\' WHERE priority IS NULL'))
        connection.execute(text('UPDATE "donation" SET purpose = \'general\' WHERE purpose IS NULL'))
        connection.execute(text('UPDATE "booking" SET location = \'Not added\' WHERE location IS NULL OR location = \'\''))
        for table_name in ("user", "case", "booking", "donation"):
            connection.execute(text(f'UPDATE "{table_name}" SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL'))


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


def current_user():
    if "user_id" not in session:
        return None
    return User.query.get(session["user_id"])


@app.context_processor
def inject_template_globals():
    return {"current_user": current_user()}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_youtube_videos():
    fallback = ["nFREfeW3P7M", "7X8II6J-6mU", "hT_nvWreIhg", "ysz5S6PUM-U"]
    api_key = app.config.get("YOUTUBE_API_KEY")
    if not api_key:
        return fallback
    try:
        response = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "part": "snippet",
                "q": "orphan welfare India children NGO charity",
                "type": "video",
                "videoEmbeddable": "true",
                "videoSyndicated": "true",
                "regionCode": "IN",
                "relevanceLanguage": "hi",
                "maxResults": 6,
                "key": api_key,
            },
            timeout=6,
        )
        response.raise_for_status()
        data = response.json()
        items = data.get("items", [])
        if not items:
            response2 = requests.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    "part": "snippet",
                    "q": "child welfare India",
                    "type": "video",
                    "videoEmbeddable": "true",
                    "videoSyndicated": "true",
                    "regionCode": "IN",
                    "maxResults": 6,
                    "key": api_key,
                },
                timeout=6,
            )
            response2.raise_for_status()
            items = response2.json().get("items", [])
        return [item["id"]["videoId"] for item in items if item.get("id", {}).get("videoId")] or fallback
    except requests.RequestException:
        return fallback


def get_recommended_orphanages(location="India"):
    """Use Google Places API (Text Search) to find real orphanages / children homes near the given location."""
    api_key = app.config.get("GOOGLE_API_KEY")
    if not api_key:
        return []
    query = f"orphanages near {location}"
    try:
        response = requests.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params={
                "query": query,
                "key": api_key,
                "region": "in",
            },
            timeout=8,
        )
        response.raise_for_status()
        results = response.json().get("results", [])
        orphanages = []
        for place in results[:8]:
            orphanages.append(
                {
                    "name": place.get("name", "Unknown"),
                    "address": place.get("formatted_address", location),
                    "city": location,
                    "location": place.get("formatted_address", location),
                    "contact": place.get("formatted_phone_number", "Contact via Google Maps"),
                    "rating": place.get("rating"),
                    "place_id": place.get("place_id"),
                    "map_url": f"https://www.google.com/maps/place/?q=place_id:{place.get('place_id')}",
                }
            )
        return orphanages
    except requests.RequestException:
        return []


def get_disaster_affairs():
    fallback = [
        {
            "title": "Flood preparedness update",
            "source": "OurHome Desk",
            "url": "https://ndma.gov.in/",
            "summary": "Track official advisories before donating or volunteering.",
        },
        {
            "title": "Earthquake response readiness",
            "source": "OurHome Desk",
            "url": "https://ndma.gov.in/",
            "summary": "Use verified emergency channels and local updates.",
        },
        {
            "title": "Cyclone and coastal alerts",
            "source": "OurHome Desk",
            "url": "https://mausam.imd.gov.in/",
            "summary": "Follow IMD warnings for coastal evacuation and relief needs.",
        },
    ]
    try:
        response = requests.get(
            "https://api.gdeltproject.org/api/v2/doc/doc",
            params={
                "query": "(flood OR earthquake OR tsunami OR cyclone) sourceCountry:IN",
                "mode": "artlist",
                "format": "json",
                "maxrecords": 10,
                "sort": "hybridrel",
            },
            timeout=5,
        )
        response.raise_for_status()
        articles = response.json().get("articles", [])
    except (requests.RequestException, ValueError):
        return fallback

    return [
        {
            "title": article.get("title", "India disaster update"),
            "source": article.get("sourceCommonName", "News source"),
            "url": article.get("url", "#"),
            "summary": article.get("seendate", "Latest verified current affair"),
        }
        for article in articles[:8]
    ] or fallback


def send_reset_email(user, reset_url):
    if not app.config.get("SMTP_HOST"):
        return False
    message = EmailMessage()
    message["Subject"] = "Reset your OurHome password"
    message["From"] = app.config["SMTP_FROM"]
    message["To"] = user.email
    message.set_content(
        f"Hi {user.name},\n\nReset your OurHome password here:\n{reset_url}\n\nThis link expires in 30 minutes."
    )
    try:
        with smtplib.SMTP(app.config["SMTP_HOST"], app.config["SMTP_PORT"]) as server:
            server.starttls()
            if app.config.get("SMTP_USERNAME"):
                server.login(app.config["SMTP_USERNAME"], app.config["SMTP_PASSWORD"])
            server.send_message(message)
        return True
    except (smtplib.SMTPException, ConnectionError):
        return False


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session.clear()
            session["user_id"] = user.id
            flash("Welcome back.", "success")
            return redirect(url_for("dashboard"))
        flash("Incorrect email or password.", "error")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        mobile = request.form.get("mobile", "").strip()
        location = request.form.get("location", "").strip()
        password = request.form.get("password", "")
        if not name or not mobile or not location:
            flash("Name, mobile number, and location are required.", "error")
            return render_template("register.html")
        if len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
            return render_template("register.html")
        if User.query.filter_by(email=email).first():
            flash("This email is already registered.", "error")
            return render_template("register.html")
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        db.session.add(User(name=name, email=email, mobile=mobile, location=location, password=hashed_password))
        db.session.commit()
        flash("Account created. Please sign in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if user:
            user.reset_token = secrets.token_urlsafe(32)
            user.reset_expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=30)
            db.session.commit()
            reset_url = url_for("reset_password", token=user.reset_token, _external=True)
            if send_reset_email(user, reset_url):
                flash("Password reset link sent to your email.", "success")
            else:
                flash(f"Development reset link: {reset_url}", "success")
        else:
            flash("If this email is registered, a reset link will be sent.", "success")
    return render_template("forgot_password.html")


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    if not user or not user.reset_expires_at or user.reset_expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        flash("This reset link is invalid or expired.", "error")
        return redirect(url_for("forgot_password"))
    if request.method == "POST":
        password = request.form.get("password", "")
        if len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
            return render_template("reset_password.html")
        user.password = bcrypt.generate_password_hash(password).decode("utf-8")
        user.reset_token = None
        user.reset_expires_at = None
        db.session.commit()
        flash("Password updated. Please sign in.", "success")
        return redirect(url_for("login"))
    return render_template("reset_password.html")


@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    user_location = user.location if user and user.location else "India"
    return render_template(
        "dashboard.html",
        videos=get_youtube_videos(),
        active_cases=Case.query.filter_by(status="active").count(),
        inactive_cases=Case.query.filter_by(status="inactive").count(),
        total_donations=db.session.query(func.coalesce(func.sum(Donation.amount), 0)).scalar(),
        upcoming_bookings=Booking.query.filter_by(user_id=session["user_id"]).order_by(Booking.date.asc()).limit(4).all(),
        affairs=get_disaster_affairs(),
        recommended_orphanages=get_recommended_orphanages(user_location),
    )


@app.route("/profile")
@login_required
def profile():
    user_id = session["user_id"]
    return render_template(
        "profile.html",
        user_cases=Case.query.filter_by(user_id=user_id).order_by(Case.created_at.desc()).all(),
        donations=Donation.query.filter_by(user_id=user_id).order_by(Donation.created_at.desc()).all(),
        bookings=Booking.query.filter_by(user_id=user_id).order_by(Booking.created_at.desc()).all(),
    )


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("login"))


@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        file = request.files.get("image")
        if not file or not file.filename or not allowed_file(file.filename):
            flash("Upload a PNG, JPG, JPEG, or WEBP image.", "error")
            return render_template("upload.html")
        filename = secure_filename(file.filename)
        stored_name = f"{session['user_id']}_{secrets.token_hex(6)}_{filename}"
        upload_path = os.path.join(app.config["UPLOAD_FOLDER"], stored_name)
        file.save(upload_path)
        db.session.add(
            Case(
                user_id=session["user_id"],
                image=upload_path.replace("\\", "/"),
                location=request.form.get("location", "").strip(),
                description=request.form.get("condition", "").strip(),
                priority=request.form.get("priority", "medium"),
            )
        )
        db.session.commit()
        flash("Case report submitted.", "success")
        return redirect(url_for("cases"))
    return render_template("upload.html")


@app.route("/cases")
@login_required
def cases():
    status = request.args.get("status", "active")
    query = Case.query
    if status in {"active", "inactive"}:
        query = query.filter_by(status=status)
    return render_template("cases.html", cases=query.order_by(Case.created_at.desc()).all(), status=status)


@app.post("/cases/<int:case_id>/archive")
@login_required
def archive_case(case_id):
    case = Case.query.get_or_404(case_id)
    if case.user_id != session["user_id"]:
        flash("Only the uploader can mark this case inactive.", "error")
        return redirect(url_for("cases"))
    case.status = "inactive"
    db.session.commit()
    flash("Case marked inactive.", "success")
    return redirect(url_for("cases"))


@app.route("/donate", methods=["POST"])
@login_required
def donate():
    amount = int(request.form.get("amount", 0))
    if amount < 1:
        flash("Enter a valid donation amount.", "error")
        return redirect(url_for("dashboard"))
    db.session.add(Donation(user_id=session["user_id"], amount=amount, purpose=request.form.get("purpose", "general")))
    db.session.commit()
    flash("Donation record saved. Complete payment only on the official PM CARES page.", "success")
    return redirect(url_for("dashboard"))


@app.route("/booking", methods=["GET", "POST"])
@login_required
def booking():
    if request.method == "POST":
        db.session.add(
            Booking(
                user_id=session["user_id"],
                orphanage=request.form.get("name", "").strip(),
                location=request.form.get("location", "").strip(),
                date=request.form.get("date", ""),
                slot=request.form.get("slot", ""),
                notes=request.form.get("notes", "").strip(),
            )
        )
        db.session.commit()
        flash("Food donation slot booked.", "success")
        return redirect(url_for("dashboard"))
    return render_template("booking.html")


@app.route("/enquiry")
@login_required
def enquiry():
    search = request.args.get("q", "").strip().lower()
    partners = ORPHANAGES
    if search:
        api_partners = get_recommended_orphanages(search)
        if api_partners:
            partners = api_partners
        else:
            partners = [
                orphanage
                for orphanage in ORPHANAGES
                if search in orphanage["name"].lower()
                or search in orphanage["city"].lower()
                or search in orphanage["location"].lower()
            ]
    booked_slots = {}
    for booking_row in Booking.query.all():
        booked_slots.setdefault(booking_row.orphanage, {}).setdefault(booking_row.date, []).append(booking_row.slot)
    calendar_dates = [(datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=day)).strftime("%Y-%m-%d") for day in range(7)]
    return render_template(
        "enquiry.html",
        partners=partners,
        search=search,
        booked_slots=booked_slots,
        calendar_dates=calendar_dates,
    )


@app.get("/api/cases")
@login_required
def api_cases():
    return jsonify(
        [
            {
                "id": case.id,
                "location": case.location,
                "condition": case.description,
                "status": case.status,
                "priority": case.priority,
                "image": case.image,
                "uploader": case.reporter.name,
                "contact": case.reporter.mobile,
                "created_at": case.created_at.isoformat(),
            }
            for case in Case.query.order_by(Case.created_at.desc()).all()
        ]
    )


@app.get("/api/metrics")
@login_required
def api_metrics():
    return jsonify(
        {
            "active_cases": Case.query.filter_by(status="active").count(),
            "inactive_cases": Case.query.filter_by(status="inactive").count(),
            "donation_total": db.session.query(func.coalesce(func.sum(Donation.amount), 0)).scalar(),
            "bookings": Booking.query.count(),
        }
    )


if __name__ == "__main__":
    with app.app_context():
        initialize_database()
    app.run(debug=True, use_reloader=False)

