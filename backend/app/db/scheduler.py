from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

from app.db.database import engine, SQLALCHEMY_DATABASE_URL


Scheduler = BackgroundScheduler(
    jobstores={
        'default': SQLAlchemyJobStore(url=SQLALCHEMY_DATABASE_URL, engine=engine)
    },
    executors={'default': ThreadPoolExecutor(20)},
    job_defaults={'coalesce': True, 'misfire_grace_time': 60 * 10},
    misfire_grace_time=600,
)
