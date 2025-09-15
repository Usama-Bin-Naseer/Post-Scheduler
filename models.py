# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    image = db.Column(db.String(120), nullable=False)
    schedule_time = db.Column(db.DateTime, nullable=False)
    published = db.Column(db.Boolean, default=False)  # New field to track if the post is published

    def __repr__(self):
        return f"Post('{self.text}', '{self.image}', '{self.schedule_time}', '{self.published}')"
