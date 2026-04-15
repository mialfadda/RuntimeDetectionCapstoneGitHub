from celery import Celery
from app import create_app

def make_celery(app):
    celery = Celery(
        app.import_name,
        broker='redis://localhost:6379/0',
        backend='redis://localhost:6379/0'
    )

    # This makes Celery tasks run inside Flask app context
    # so they can access the database
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

# Create the Flask app and Celery instance
flask_app = create_app()
celery = make_celery(flask_app)