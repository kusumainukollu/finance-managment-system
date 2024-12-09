from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users_new'  # Make sure the table name is correct
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    username = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(20))
    company = db.Column(db.String(100))
    dob = db.Column(db.String(20))
    password = db.Column(db.String(100))

    # Define the relationship to Transactions
    transactions = db.relationship('Transactions', back_populates='user')
    # Define the relationship to UserBudget
    budgets = db.relationship('UserBudget', back_populates='user', uselist=False)

class UserBudget(db.Model):
    __tablename__ = 'user_budgets'  # Ensure this table name matches the database
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users_new.id'), nullable=False)
    food = db.Column(db.Float, default=0)
    transport = db.Column(db.Float, default=0)
    entertainment = db.Column(db.Float, default=0)
    bills = db.Column(db.Float, default=0)
    other = db.Column(db.Float, default=0)

    # Define the relationship back to User
    user = db.relationship('User', back_populates='budgets')

class Transactions(db.Model):
    __tablename__ = 'transactions'  # Make sure this table name matches the database
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10), nullable=False)
    type = db.Column(db.String(10), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('users_new.id'), nullable=False)
    
    # Define the relationship back to User
    user = db.relationship('User', back_populates='transactions')
