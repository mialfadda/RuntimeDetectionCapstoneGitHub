# Celery configuration
# Redis is used as the message broker
# This means Celery sends tasks TO Redis
# and workers pick them up FROM Redis

class CeleryConfig:
    # where Celery sends tasks to
    broker_url = 'redis://localhost:6379/0'

    # where Celery stores results
    result_backend = 'redis://localhost:6379/0'

    # task settings
    task_serializer = 'json'
    result_serializer = 'json'
    accept_content = ['json']
    timezone = 'UTC'
    enable_utc = True

    # task routing — which tasks go to which queue
    task_routes = {
        'app.tasks.scan_url': {'queue': 'scanning'},
        'app.tasks.generate_report': {'queue': 'reports'},
        'app.tasks.retrain_model': {'queue': 'models'},
    }