# src/models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class Blacklist(db.Model):
    __tablename__ = "blacklists"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(320), unique=True, nullable=False)
    app_uuid = db.Column(db.String(36), nullable=False)
    blocked_reason = db.Column(db.String(255))
    request_ip = db.Column(db.String(45))  # IPv6 máx 45
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
