from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class LCV(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    capacity = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<LCV {self.id}>'
