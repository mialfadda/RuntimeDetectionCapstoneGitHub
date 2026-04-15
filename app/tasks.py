from celery import shared_task
from datetime import datetime

@shared_task(bind=True, max_retries=3)
def scan_url(self, submission_id):
    try:
        from app import create_app
        from app.database.models import db, URLSubmission
        app = create_app()
        with app.app_context():
            submission = URLSubmission.query.get(submission_id)
            if not submission:
                return {'error': f'Submission {submission_id} not found'}
            submission.status = 'complete'
            db.session.commit()
            return {'submission_id': submission_id, 'status': 'complete'}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)

@shared_task(bind=True)
def batch_scan_urls(self, submission_ids):
    results = []
    for submission_id in submission_ids:
        task = scan_url.delay(submission_id)
        results.append({'submission_id': submission_id, 'task_id': task.id, 'status': 'queued'})
    return {'total': len(submission_ids), 'queued': results}

@shared_task(bind=True, max_retries=3)
def generate_report(self, prediction_id, format='PDF'):
    try:
        from app import create_app
        from app.database.models import db, Prediction, Reports
        app = create_app()
        with app.app_context():
            prediction = Prediction.query.get(prediction_id)
            if not prediction:
                return {'error': f'Prediction {prediction_id} not found'}
            report = Reports(
                predictionID=prediction_id,
                format=format,
                status='complete',
                threatLevel='high' if prediction.label == 'phishing' else 'low',
                summary=f'URL scanned with {prediction.confidence}% confidence. Result: {prediction.label}',
                generationTime=datetime.utcnow()
            )
            db.session.add(report)
            db.session.commit()
            return {'report_id': report.reportID, 'status': 'complete'}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)

@shared_task(bind=True)
def retrain_model(self, model_id):
    try:
        from app import create_app
        from app.database.models import db, Model
        app = create_app()
        with app.app_context():
            model = Model.query.get(model_id)
            if not model:
                return {'error': f'Model {model_id} not found'}
            return {'model_id': model_id, 'model_name': model.name, 'status': 'retraining_started'}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=300)