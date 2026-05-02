from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=_now, nullable=False)


class User(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, default="")
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    mobile = db.Column(db.String(20), nullable=False, default="")
    location = db.Column(db.String(140), nullable=False, default="")
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), default="volunteer", nullable=False)
    reset_token = db.Column(db.String(120), unique=True)
    reset_expires_at = db.Column(db.DateTime)

    cases = db.relationship("Case", backref="reporter", lazy=True)
    bookings = db.relationship("Booking", backref="volunteer", lazy=True)
    donations = db.relationship("Donation", backref="donor", lazy=True)


class Case(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    image = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(140), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), default="active", nullable=False, index=True)
    priority = db.Column(db.String(20), default="medium", nullable=False)


class Booking(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    orphanage = db.Column(db.String(140), nullable=False)
    location = db.Column(db.String(140), nullable=False, default="")
    date = db.Column(db.String(50), nullable=False)
    slot = db.Column(db.String(30), nullable=False)
    notes = db.Column(db.String(255))


class Donation(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    purpose = db.Column(db.String(80), default="general", nullable=False)

