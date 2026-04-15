from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy.orm import validates

db = SQLAlchemy()

#I will be creating the database that connects to flask based off of the ERD planned last semester
#The ERD Link:
#https://docs.google.com/document/d/1zEwd5muICKydc-gZ5ZnfxAZn2o9ANYdM7EV2-4bbDPs/edit?tab=t.0#heading=h.yjq4ks9itxqm
#https://www.geeksforgeeks.org/python/connect-flask-to-a-database-with-flask-sqlalchemy/
#I used this to help figure out how to write the python code for the tables


# ─── 1. USER ────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = 'users'

    userID       = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(100), nullable=False)
    email        = db.Column(db.String(150), nullable=False, unique=True)
    role         = db.Column(db.String(100), default='user')
    passwordHash = db.Column(db.String(300), nullable=False)

    # 1 User submits many URLSubmissions
    # if user deleted all their submissions will be deleted as well
    submissions = db.relationship('URLSubmission', backref='user',
                                  lazy=True, cascade='all, delete-orphan')

    # Validations
    @validates('email')
    def validate_email(self, key, email):
        assert '@' in email, 'Invalid email address'
        return email

    @validates('role')
    def validate_role(self, key, role):
        assert role in ['user', 'admin'], 'Role must be user or admin'
        return role

    # Helper methods
    @classmethod
    def get_by_email(cls, email):
        return cls.query.filter_by(email=email).first()
        # use: User.get_by_email('test@test.com')

    @classmethod
    def get_all_users(cls):
        return cls.query.filter_by(role='user').all()
        # use: User.get_all_users()

    def __repr__(self):
        return f'<User {self.name} - {self.email}>'


# ─── 2. ADMIN ───────────────────────────────────────────────
class Admin(db.Model):
    __tablename__ = 'admins'

    adminID          = db.Column(db.Integer, primary_key=True)
    approvalID       = db.Column(db.Integer)
    status           = db.Column(db.String(100), nullable=False)
    lastLogin        = db.Column(db.DateTime, nullable=False)
    privilegeControl = db.Column(db.String(300), nullable=False)

    # FK — if the User is deleted, their Admin record is deleted too
    userID = db.Column(db.Integer, db.ForeignKey('users.userID',
                       ondelete='CASCADE'), nullable=False)

    # 1 Admin records many ActionLogs
    # if Admin deleted, all their action logs deleted too
    recordsActionLogs = db.relationship('ActionLog', backref='admin',
                                        lazy=True, cascade='all, delete-orphan')

    # many to many — Admin grants permissions to Users
    # if Admin deleted, all permissions they granted are deleted too
    grantsPermissions = db.relationship('GrantsPermission', backref='admin',
                                        lazy=True, cascade='all, delete-orphan')

    # many to many — Admin manages Users
    # if Admin deleted, all their manage records deleted too
    manages = db.relationship('Manages', backref='managedByAdmin',
                              lazy=True, cascade='all, delete-orphan')

    # 1 Admin approves many ModelVersions
    approvesModelVersions = db.relationship('ModelVersion', backref='approvedByAdmin',
                                            lazy=True)

    # 1 Admin records many URLSubmissions
    recordsURLSubmissions = db.relationship('URLSubmission', backref='recordedByAdmin',
                                            lazy=True)

    # Validations
    @validates('status')
    def validate_status(self, key, status):
        # only 'active' or 'inactive' allowed
        assert status in ['active', 'inactive'], 'Status must be active or inactive'
        return status

    # Helper methods
    @classmethod
    def get_active_admins(cls):
        return cls.query.filter_by(status='active').all()
        # use: Admin.get_active_admins()

    @classmethod
    def get_by_user(cls, userID):
        return cls.query.filter_by(userID=userID).first()
        # use: Admin.get_by_user(5)

    def __repr__(self):
        return f'<Admin {self.adminID} - {self.status}>'


# ─── 3. ACTION LOG ──────────────────────────────────────────
class ActionLog(db.Model):
    __tablename__ = 'actionLogs'

    actionID     = db.Column(db.Integer, primary_key=True)
    action       = db.Column(db.String(100), nullable=False)
    target       = db.Column(db.String(100))
    exportType   = db.Column(db.String(50))
    creationDate = db.Column(db.DateTime, default=datetime.utcnow)

    # FK — if Admin deleted, their action logs are deleted too
    adminID = db.Column(db.Integer, db.ForeignKey('admins.adminID',
                        ondelete='CASCADE'), nullable=False)

    # Validations
    @validates('action')
    def validate_action(self, key, action):
        # only these 6 specific actions are allowed
        # prevents typos like 'Login' or 'LOG_IN' breaking your data
        valid = ['login', 'logout', 'submit_url', 'override', 'export', 'delete']
        assert action in valid, f'Action must be one of {valid}'
        return action

    # Helper methods
    @classmethod
    def get_by_admin(cls, adminID):
        return cls.query.filter_by(adminID=adminID).all()
        # use: ActionLog.get_by_admin(1)

    @classmethod
    def get_by_action_type(cls, action):
        return cls.query.filter_by(action=action).all()
        # use: ActionLog.get_by_action_type('login')

    def __repr__(self):
        return f'<ActionLog {self.actionID} - {self.action}>'


# ─── 4. URL SUBMISSION ──────────────────────────────────────
class URLSubmission(db.Model):
    __tablename__ = 'urlSubmissions'

    submissionID     = db.Column(db.Integer, primary_key=True)
    url              = db.Column(db.String(3000), nullable=False)
    creationDate     = db.Column(db.DateTime, default=datetime.utcnow)
    submissionSource = db.Column(db.String(100))
    status           = db.Column(db.String(50), default='pending')

    # FK — if User deleted, their submissions deleted too
    userID = db.Column(db.Integer, db.ForeignKey('users.userID',
                       ondelete='CASCADE'), nullable=False)

    # FK — if Admin deleted, submission stays but adminID becomes NULL
    # we don't want to lose the submission just because an admin was removed
    adminID = db.Column(db.Integer, db.ForeignKey('admins.adminID',
                        ondelete='SET NULL'))

    # FK — many submissions can point to 1 website (many to 1)
    # if website deleted, submission stays but websiteID becomes NULL
    websiteID = db.Column(db.Integer, db.ForeignKey('websites.websiteID',
                          ondelete='SET NULL'))

    # Validations
    @validates('status')
    def validate_status(self, key, status):
        # prevents any other status value being saved
        assert status in ['pending', 'complete', 'failed'], \
            'Status must be pending, complete or failed'
        return status

    @validates('url')
    def validate_url(self, key, url):
        # makes sure every URL is properly formatted before saving
        assert url.startswith('http://') or url.startswith('https://'), \
            'URL must start with http:// or https://'
        return url

    # Helper methods
    @classmethod
    def get_by_status(cls, status):
        return cls.query.filter_by(status=status).all()
        # use: URLSubmission.get_by_status('pending')

    @classmethod
    def get_by_user(cls, userID):
        return cls.query.filter_by(userID=userID).all()
        # use: URLSubmission.get_by_user(5)

    @classmethod
    def get_pending(cls):
        return cls.query.filter_by(status='pending').all()
        # use: URLSubmission.get_pending()

    def __repr__(self):
        return f'<URLSubmission {self.submissionID} - {self.url}>'


# ─── 5. WEBSITE ─────────────────────────────────────────────
class Website(db.Model):
    __tablename__ = 'websites'

    websiteID      = db.Column(db.Integer, primary_key=True)
    rootDomain     = db.Column(db.String(300), nullable=False, unique=True)
    topLevelDomain = db.Column(db.String(300))
    # unique=True means the same domain can't be stored twice
    # nullable=False means rootDomain is required

    # 1 Website has many URLSubmissions pointing to it
    # many-to-1 — many submissions point to 1 website
    submissions = db.relationship('URLSubmission', backref='website', lazy=True)

    # 1 Website is analyzed in many SandboxSessions
    # if Website deleted, all its sandbox sessions deleted too
    sandboxSessions = db.relationship('SandboxSession', backref='website',
                                      lazy=True, cascade='all, delete-orphan')

    # Helper methods
    @classmethod
    def get_by_domain(cls, domain):
        return cls.query.filter_by(rootDomain=domain).first()
        # use: Website.get_by_domain('evil.com')

    @classmethod
    def get_or_create(cls, rootDomain, topLevelDomain):
        # checks if website exists first, creates it if not
        # prevents duplicate entries for the same domain
        website = cls.get_by_domain(rootDomain)
        if not website:
            website = cls(rootDomain=rootDomain,
                         topLevelDomain=topLevelDomain)
            db.session.add(website)
            db.session.commit()
        return website

    def __repr__(self):
        return f'<Website {self.websiteID} - {self.rootDomain}>'


# ─── 6. SANDBOX SESSION ─────────────────────────────────────
class SandboxSession(db.Model):
    __tablename__ = 'sandboxSessions'

    sessionID  = db.Column(db.Integer, primary_key=True)
    isIsolated = db.Column(db.Boolean, default=True)
    engine     = db.Column(db.String(100))
    startTime  = db.Column(db.DateTime)
    endTime    = db.Column(db.DateTime)
    status     = db.Column(db.String(100), default='pending')

    # FK — if Website deleted, all its sandbox sessions deleted too
    websiteID = db.Column(db.Integer, db.ForeignKey('websites.websiteID',
                          ondelete='CASCADE'), nullable=False)

    # 1 SandboxSession produces many Predictions
    # if SandboxSession deleted, all its predictions deleted too
    predictions = db.relationship('Prediction', backref='sandboxSession',
                                  lazy=True, cascade='all, delete-orphan')

    # Validations
    @validates('status')
    def validate_status(self, key, status):
        assert status in ['pending', 'running', 'complete', 'failed'], \
            'Invalid status'
        return status

    # Helper methods
    @classmethod
    def get_by_status(cls, status):
        return cls.query.filter_by(status=status).all()

    @classmethod
    def get_by_website(cls, websiteID):
        return cls.query.filter_by(websiteID=websiteID).all()
        # use: SandboxSession.get_by_website(1)

    def __repr__(self):
        return f'<SandboxSession {self.sessionID} - {self.status}>'


# ─── 7. MODEL ───────────────────────────────────────────────
class Model(db.Model):
    __tablename__ = 'models'

    modelID     = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False, unique=True)
    modelFamily = db.Column(db.String(100))
    framework   = db.Column(db.String(100))
    # unique=True means no two models can have the same name

    # 1 Model has many ModelVersions
    # if Model deleted, all its versions deleted too
    versions = db.relationship('ModelVersion', backref='model',
                               lazy=True, cascade='all, delete-orphan')

    # Helper methods
    @classmethod
    def get_by_name(cls, name):
        return cls.query.filter_by(name=name).first()
        # use: Model.get_by_name('PhishDetect')

    @classmethod
    def get_all_models(cls):
        return cls.query.all()

    def __repr__(self):
        return f'<Model {self.modelID} - {self.name}>'


# ─── 8. MODEL VERSION ───────────────────────────────────────
class ModelVersion(db.Model):
    __tablename__ = 'modelVersions'

    versionID         = db.Column(db.Integer, primary_key=True)
    versionTag        = db.Column(db.String(100))
    status            = db.Column(db.String(100), default='pending')
    accuracy          = db.Column(db.Float)
    creationTimeStamp = db.Column(db.DateTime, default=datetime.utcnow)

    # FK — if Model deleted, all its versions deleted too
    modelID = db.Column(db.Integer, db.ForeignKey('models.modelID',
                        ondelete='CASCADE'), nullable=False)

    # FK — if Admin deleted, version stays but adminID becomes NULL
    adminID = db.Column(db.Integer, db.ForeignKey('admins.adminID',
                        ondelete='SET NULL'))

    # 1 ModelVersion generates many Predictions
    predictions = db.relationship('Prediction', backref='modelVersion', lazy=True)

    # Validations
    @validates('status')
    def validate_status(self, key, status):
        assert status in ['pending', 'active', 'retired'], \
            'Status must be pending, active or retired'
        return status

    @validates('accuracy')
    def validate_accuracy(self, key, accuracy):
        # accuracy is a percentage 0-100
        if accuracy is not None:
            assert 0.0 <= accuracy <= 100.0, 'Accuracy must be between 0 and 100'
        return accuracy

    # Helper methods
    @classmethod
    def get_active(cls):
        return cls.query.filter_by(status='active').all()
        # use: ModelVersion.get_active()

    @classmethod
    def get_by_model(cls, modelID):
        return cls.query.filter_by(modelID=modelID).all()
        # use: ModelVersion.get_by_model(1)

    def __repr__(self):
        return f'<ModelVersion {self.versionID} - {self.versionTag}>'


# ─── 9. PREDICTION ──────────────────────────────────────────
class Prediction(db.Model):
    __tablename__ = 'predictions'

    predictionID  = db.Column(db.Integer, primary_key=True)
    inferenceTime = db.Column(db.Float)
    confidence    = db.Column(db.Float, nullable=False)
    scoreVector   = db.Column(db.Text)
    label         = db.Column(db.String(100), nullable=False)

    # FK — RESTRICT means you CANNOT delete a ModelVersion that has predictions
    # protects your prediction history
    versionID = db.Column(db.Integer, db.ForeignKey('modelVersions.versionID',
                          ondelete='RESTRICT'), nullable=False)

    # FK — if SandboxSession deleted, its predictions deleted too
    sessionID = db.Column(db.Integer, db.ForeignKey('sandboxSessions.sessionID',
                          ondelete='CASCADE'), nullable=False)

    # 1 to 1 — uselist=False makes this one-to-one not one-to-many
    # if Prediction deleted, its explanation deleted too
    # uselist=False means prediction.explanation returns ONE object not a list
    explanation = db.relationship('Explanation', backref='prediction',
                                  uselist=False, cascade='all, delete-orphan')

    # 1 to many — if Prediction deleted, all its reports deleted too
    reports = db.relationship('Reports', backref='prediction',
                              lazy=True, cascade='all, delete-orphan')

    # Validations
    @validates('confidence')
    def validate_confidence(self, key, confidence):
        # confidence is 0-100%
        assert 0.0 <= confidence <= 100.0, 'Confidence must be between 0 and 100'
        return confidence

    @validates('label')
    def validate_label(self, key, label):
        # only these two labels are valid for your system
        assert label in ['phishing', 'legitimate'], \
            'Label must be phishing or legitimate'
        return label

    # Helper methods
    @classmethod
    def get_phishing(cls):
        return cls.query.filter_by(label='phishing').all()
        # use: Prediction.get_phishing()

    @classmethod
    def get_by_session(cls, sessionID):
        return cls.query.filter_by(sessionID=sessionID).all()

    @classmethod
    def get_high_confidence(cls, threshold=90.0):
        return cls.query.filter(cls.confidence >= threshold).all()
        # use: Prediction.get_high_confidence()

    def __repr__(self):
        return f'<Prediction {self.predictionID} - {self.label} {self.confidence}%>'


# ─── 10. EXPLANATION ────────────────────────────────────────
class Explanation(db.Model):
    __tablename__ = 'explanations'

    explanationID = db.Column(db.Integer, primary_key=True)
    rationale     = db.Column(db.Text)
    method        = db.Column(db.String(50))
    creationTime  = db.Column(db.DateTime, default=datetime.utcnow)

    # FK — unique=True enforces the 1-to-1 — only ONE explanation per prediction
    # if Prediction deleted, its explanation deleted too
    predictionID = db.Column(db.Integer, db.ForeignKey('predictions.predictionID',
                             ondelete='CASCADE'), nullable=False, unique=True)

    # Validations
    @validates('method')
    def validate_method(self, key, method):
        # your system only uses SHAP or LIME for explainability
        assert method in ['SHAP', 'LIME'], 'Method must be SHAP or LIME'
        return method

    # Helper methods
    @classmethod
    def get_by_method(cls, method):
        return cls.query.filter_by(method=method).all()

    @classmethod
    def get_by_prediction(cls, predictionID):
        return cls.query.filter_by(predictionID=predictionID).first()

    def __repr__(self):
        return f'<Explanation {self.explanationID} - {self.method}>'


# ─── 11. REPORTS ────────────────────────────────────────────
class Reports(db.Model):
    __tablename__ = 'reports'

    reportID       = db.Column(db.Integer, primary_key=True)
    generationTime = db.Column(db.DateTime, default=datetime.utcnow)
    threatLevel    = db.Column(db.String(100))
    status         = db.Column(db.String(100), default='pending')
    summary        = db.Column(db.Text)
    format         = db.Column(db.String(100))

    # FK — if Prediction deleted, all its reports deleted too
    predictionID = db.Column(db.Integer, db.ForeignKey('predictions.predictionID',
                             ondelete='CASCADE'), nullable=False)

    # Validations
    @validates('format')
    def validate_format(self, key, format):
        assert format in ['PDF', 'CSV'], 'Format must be PDF or CSV'
        return format

    @validates('threatLevel')
    def validate_threat_level(self, key, threatLevel):
        if threatLevel is not None:
            valid = ['low', 'medium', 'high', 'critical']
            assert threatLevel in valid, f'Threat level must be one of {valid}'
        return threatLevel

    # Helper methods
    @classmethod
    def get_by_threat_level(cls, level):
        return cls.query.filter_by(threatLevel=level).all()

    @classmethod
    def get_by_format(cls, format):
        return cls.query.filter_by(format=format).all()

    def __repr__(self):
        return f'<Reports {self.reportID} - {self.threatLevel}>'


# ─── 12. GRANTS PERMISSION ──────────────────────────────────
class GrantsPermission(db.Model):
    __tablename__ = 'grantsPermissions'

    permissionID = db.Column(db.Integer, primary_key=True)
    resource     = db.Column(db.String(300))
    action       = db.Column(db.String(300))

    # FK — if either Admin or User deleted, the permission record is deleted too
    adminID = db.Column(db.Integer, db.ForeignKey('admins.adminID',
                        ondelete='CASCADE'), nullable=False)
    userID  = db.Column(db.Integer, db.ForeignKey('users.userID',
                        ondelete='CASCADE'), nullable=False)

    # Helper methods
    @classmethod
    def get_by_admin(cls, adminID):
        return cls.query.filter_by(adminID=adminID).all()

    @classmethod
    def get_by_user(cls, userID):
        return cls.query.filter_by(userID=userID).all()

    def __repr__(self):
        return f'<GrantsPermission {self.permissionID} - {self.resource}>'


# ─── 13. MANAGES ────────────────────────────────────────────
class Manages(db.Model):
    __tablename__ = 'manages'

    manageID        = db.Column(db.Integer, primary_key=True)
    roleID          = db.Column(db.Integer)
    roleName        = db.Column(db.String(100))
    roleDescription = db.Column(db.String(300))

    # FK — if either Admin or User deleted, the manage record is deleted too
    adminID = db.Column(db.Integer, db.ForeignKey('admins.adminID',
                        ondelete='CASCADE'), nullable=False)
    userID  = db.Column(db.Integer, db.ForeignKey('users.userID',
                        ondelete='CASCADE'), nullable=False)

    # Helper methods
    @classmethod
    def get_by_admin(cls, adminID):
        return cls.query.filter_by(adminID=adminID).all()

    @classmethod
    def get_users_managed_by(cls, adminID):
        return cls.query.filter_by(adminID=adminID).all()

    def __repr__(self):
        return f'<Manages {self.manageID} - {self.roleName}>'


# ─── 14. API KEY ────────────────────────────────────────────
# owned by A1 (Step 36) — only the SHA-256 hash of the key is stored
class ApiKey(db.Model):
    __tablename__ = 'apiKeys'

    keyID      = db.Column(db.Integer, primary_key=True)
    keyHash    = db.Column(db.String(128), nullable=False, unique=True)
    label      = db.Column(db.String(100))
    createdAt  = db.Column(db.DateTime, default=datetime.utcnow)
    lastUsedAt = db.Column(db.DateTime)
    usageCount = db.Column(db.Integer, default=0)
    revoked    = db.Column(db.Boolean, default=False)

    # FK
    userID = db.Column(db.Integer, db.ForeignKey('users.userID',
                       ondelete='CASCADE'), nullable=False)

    def __repr__(self):
        return f'<ApiKey {self.keyID} - {self.label}>'


# ─── 15. RATE LIMIT VIOLATION ───────────────────────────────
# owned by A1 (Step 12)
class RateLimitViolation(db.Model):
    __tablename__ = 'rateLimitViolations'

    violationID  = db.Column(db.Integer, primary_key=True)
    ipAddress    = db.Column(db.String(64))
    endpoint     = db.Column(db.String(200))
    creationDate = db.Column(db.DateTime, default=datetime.utcnow)

    # FK
    userID = db.Column(db.Integer, db.ForeignKey('users.userID',
                       ondelete='SET NULL'))

    def __repr__(self):
        return f'<RateLimitViolation {self.violationID} - {self.ipAddress}>'