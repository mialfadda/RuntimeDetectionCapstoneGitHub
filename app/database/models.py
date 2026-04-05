from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

#I will be creating the database that connects to flask based off of the ERD planned last semester
#The ERD Link:
#https://docs.google.com/document/d/1zEwd5muICKydc-gZ5ZnfxAZn2o9ANYdM7EV2-4bbDPs/edit?tab=t.0#heading=h.yjq4ks9itxqm
#https://www.geeksforgeeks.org/python/connect-flask-to-a-database-with-flask-sqlalchemy/
#I used this to help figure out how to write the python code for the tables

#user
class User(db.Model):
    __tablename__ = 'users'
    userID = db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    role=db.Column(db.String(100), default='user')
    passwordHash = db.Column(db.String(300), nullable=False)

    #Relationships
    submissions = db.relationship('URLSubmission', backref='user', lazy=True)

#admin
class Admin(db.Model):
    __tablename__ = 'admins'
    adminID = db.Column(db.Integer, primary_key=True)
    status=db.Column(db.String(100), nullable=False)
    lastLogin = db.Column(db.DateTime,nullable=False)
    privelegeControl=db.Column(db.String(300), nullable=False)

    #FK
    userID = db.Column(db.Integer, db.ForeignKey('users.userID'), nullable=False)

    #relationships
    recordsActionLogs=db.relationship('ActionLog', backref='admin', lazy='True')
    grantsPermissions=db.relationship('GrantsPermission', backref='admin', lazy='True')
    approvesModelVersions=db.relationship('ModelVersion', backref='admin', lazy='True')
    recordsURLSubmissions=db.relationship('URLSubmission', backref='admin', lazy='True')
    manages=db.relationship('Manages', backref='admin', lazy='True')

