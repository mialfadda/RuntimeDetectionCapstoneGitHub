import pytest
from datetime import datetime
from app import create_app
from app.database.models import db, User, Admin, ActionLog, URLSubmission, \
    Website, SandboxSession, ModelVersion, Model, Prediction, Explanation, \
    Reports, GrantsPermission, Manages

@pytest.fixture
def app():
    app = create_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

# ─── TEST 1 — All tables exist ───────────────────────────────
def test_tables_exist(app):
    with app.app_context():
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        assert 'users' in tables
        assert 'admins' in tables
        assert 'actionLogs' in tables
        assert 'urlSubmissions' in tables
        assert 'websites' in tables
        assert 'sandboxSessions' in tables
        assert 'modelVersions' in tables
        assert 'models' in tables
        assert 'predictions' in tables
        assert 'explanations' in tables
        assert 'reports' in tables
        assert 'grantsPermissions' in tables
        assert 'manages' in tables
        print('✅ All tables exist!')
# ─── TEST 2 — Create a User ──────────────────────────────────
def test_create_user(app):
    with app.app_context():
        user = User(
            name='Test User',
            email='test@test.com',
            role='user',
            passwordHash='hashedpassword123'
        )
        db.session.add(user)
        db.session.commit()

        found = User.query.filter_by(email='test@test.com').first()
        assert found is not None
        assert found.name == 'Test User'
        print('✅ User created successfully!')

# ─── TEST 3 — Create an Admin linked to User ─────────────────
def test_create_admin(app):
    with app.app_context():
        user = User(
            name='Admin User',
            email='admin@test.com',
            role='admin',
            passwordHash='hashedpassword123'
        )
        db.session.add(user)
        db.session.commit()

        admin = Admin(
            userID=user.userID,
            status='active',
            lastLogin=datetime.utcnow(),
            privilegeControl='full'
        )
        db.session.add(admin)
        db.session.commit()

        found = Admin.query.filter_by(userID=user.userID).first()
        assert found is not None
        assert found.status == 'active'
        print('✅ Admin created and linked to User!')

# ─── TEST 4 — Create a URL Submission ────────────────────────
def test_create_submission(app):
    with app.app_context():
        user = User(
            name='Test User',
            email='submit@test.com',
            role='user',
            passwordHash='hashedpassword123'
        )
        db.session.add(user)
        db.session.commit()

        submission = URLSubmission(
            userID=user.userID,
            url='http://suspicious-site.com',
            submissionSource='manual',
            status='pending'
        )
        db.session.add(submission)
        db.session.commit()

        found = URLSubmission.query.filter_by(url='http://suspicious-site.com').first()
        assert found is not None
        assert found.status == 'pending'
        print('✅ URL Submission created!')

# ─── TEST 5 — Full chain test ────────────────────────────────
def test_full_chain(app):
    with app.app_context():
        # Create user
        user = User(name='Chain User', email='chain@test.com',
                   role='user', passwordHash='hash123')
        db.session.add(user)
        db.session.commit()

        # Create submission
        submission = URLSubmission(userID=user.userID,
                                  url='http://evil-site.com',
                                  status='pending')
        db.session.add(submission)
        db.session.commit()

        # Create website
        website = Website(submissionID=submission.submissionID,
                         rootDomain='evil-site.com',
                         topLevelDomain='.com')
        db.session.add(website)
        db.session.commit()

        # Create sandbox session
        session = SandboxSession(websiteID=website.websiteID,
                                engine='chrome',
                                status='complete',
                                isIsolated=True)
        db.session.add(session)
        db.session.commit()

        # Create model and version
        model = Model(name='PhishDetect', modelFamily='CNN', framework='PyTorch')
        db.session.add(model)
        db.session.commit()

        version = ModelVersion(modelID=model.modelID, versionTag='v1.0',
                              status='active', accuracy=0.97)
        db.session.add(version)
        db.session.commit()

        # Create prediction
        prediction = Prediction(sessionID=session.sessionID,
                               versionID=version.versionID,
                               label='phishing',
                               confidence=0.95)
        db.session.add(prediction)
        db.session.commit()

        # Verify the full chain
        found = Prediction.query.filter_by(label='phishing').first()
        assert found is not None
        assert found.confidence == 0.95
        assert found.sandboxSession.website.rootDomain == 'evil-site.com'
        assert found.modelVersion.versionTag == 'v1.0'
        print('✅ Full chain test passed!')