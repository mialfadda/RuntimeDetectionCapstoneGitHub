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
    #attributes
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
    #attributes
    __tablename__ = 'admins'
    adminID = db.Column(db.Integer, primary_key=True)
    status=db.Column(db.String(100), nullable=False)
    lastLogin = db.Column(db.DateTime,nullable=False)
    privilegeControl=db.Column(db.String(300), nullable=False)

    #FK
    userID = db.Column(db.Integer, db.ForeignKey('users.userID'), nullable=False)

    #relationships
    recordsActionLogs=db.relationship('ActionLog', backref='admin', lazy=True)
    grantsPermissions=db.relationship('GrantsPermission', backref='admin', lazy=True)
    approvesModelVersions=db.relationship('ModelVersion', backref='approvedByAdmin', lazy=True)
    recordsURLSubmissions=db.relationship('URLSubmission', backref='recordedByAdmin', lazy=True)
    manages=db.relationship('Manages', backref='managedByAdmin', lazy=True)

#ActionLog
class ActionLog(db.Model):
    #attributes
    __tablename__ = 'actionLogs'
    actionID = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(100), nullable=False)
    target=db.Column(db.String(100))
    exportType=db.Column(db.String(50))
    creationDate = db.Column(db.DateTime,default=datetime.utcnow)

    #FK
    adminID = db.Column(db.Integer, db.ForeignKey('admins.adminID'), nullable=False)

#UrlSubmission
class URLSubmission(db.Model):
    __tablename__ = 'urlSubmissions'
    submissionID = db.Column(db.Integer, primary_key=True)
    url=db.Column(db.String(3000), nullable=False)
    creationDate = db.Column(db.DateTime,default=datetime.utcnow)
    submissionSource=db.Column(db.String(100))
    status=db.Column(db.String(50), default='pending')

    #FK
    userID = db.Column(db.Integer, db.ForeignKey('users.userID'), nullable=False)
    adminID = db.Column(db.Integer, db.ForeignKey('admins.adminID'))

    #relationships
    websites=db.relationship('Website', backref='submission', lazy=True)

#explaination
class Explanations(db.Model):
    __tablename__ = 'explanations'

    explainationID = db.Column(db.Integer, primary_key=True)
    rationale=db.Column(db.Text)
    method=db.Column(db.String(50))
    creationTime=db.Column(db.DateTime,default=datetime.utcnow)

    #FK
    predictionID = db.Column(db.Integer, db.ForeignKey('predictions.predictionID'), nullable=False)

    #Relationships
    prediction=db.relationship('Prediction', backref='explanation', lazy=True)

#website
class Website(db.Model):
    __tablename__ = 'websites'

    websiteID = db.Column(db.Integer, primary_key=True)
    rootDomain=db.Column(db.String(300))
    topLevelDomain=db.Column(db.String(300))

    #FK
    submissionID = db.Column(db.Integer, db.ForeignKey('urlSubmissions.submissionID'), nullable=False)

    #relationships
    sandboxSessions=db.relationship('SandboxSession', backref='website', lazy=True)

#modelversion
class ModelVersion(db.Model):
    __tablename__ = 'modelVersions'

    versionID = db.Column(db.Integer, primary_key=True)
    versionTag=db.Column(db.String(100))
    status=db.Column(db.String(100), default='pending')
    accuracy=db.Column(db.Float)
    creationTimeStamp = db.Column(db.DateTime,default=datetime.utcnow)

    #FK
    modelID = db.Column(db.Integer, db.ForeignKey('models.modelID'), nullable=False)
    adminID = db.Column(db.Integer, db.ForeignKey('admins.adminID'))

    #relationships
    model=db.relationship('Model', backref='versions', lazy=True)
    predictions=db.relationship('Prediction', backref='modelVersion', lazy=True)

#sandbox Session
class SandboxSession(db.Model):
    __tablename__ = 'sandboxSessions'

    sessionID = db.Column(db.Integer, primary_key=True)
    isIsolated=db.Column(db.Boolean,default=True)
    engine=db.Column(db.String(100))
    startTime=db.Column(db.DateTime)
    endTime=db.Column(db.DateTime)
    status=db.Column(db.String(100), default='pending')

    #FK
    websiteID=db.Column(db.Integer, db.ForeignKey('websites.websiteID'), nullable=False)

    #relationships
    predictions=db.relationship('Prediction', backref='sandboxSession', lazy=True)

