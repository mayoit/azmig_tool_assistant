"""
Celery background tasks for validation processing.
"""

from datetime import datetime
from celery.utils.log import get_task_logger

from workers.celery_app import celery_app
from database import SessionLocal
from models import ValidationJob, ValidationStatus
from services.validation_service import ValidationService

logger = get_task_logger(__name__)


@celery_app.task(bind=True, name="workers.tasks.run_validation")
def run_validation(self, job_id: int):
    """
    Run complete validation workflow (landing zone + servers).
    
    Args:
        job_id: Validation job ID
    """
    db = SessionLocal()
    
    logger.info(f"Starting validation job {job_id}")
    
    try:
        # Get validation job
        job = db.query(ValidationJob).filter(ValidationJob.id == job_id).first()
        if not job:
            logger.error(f"Validation job {job_id} not found")
            return {"success": False, "error": "Job not found"}
        
        # Update job status to running
        job.status = ValidationStatus.RUNNING
        job.started_at = datetime.utcnow()
        db.commit()
        
        # Create validation service
        service = ValidationService(db_session=db)
        
        # Run landing zone validation (Layer 1)
        logger.info(f"Running landing zone validation for project {job.project_id}")
        lz_result = service.validate_landing_zone(job.project_id, job_id)
        
        if not lz_result.get("success"):
            # Landing zone validation failed
            error_msg = lz_result.get("error", "Landing zone validation failed")
            job.status = ValidationStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.error_message = error_msg
            db.commit()
            service.close()
            logger.error(f"Landing zone validation failed: {error_msg}")
            return lz_result
        
        # Run server validation (Layer 2)
        logger.info(f"Running server validation for project {job.project_id}")
        server_result = service.validate_servers(job.project_id, job_id)
        
        if not server_result.get("success"):
            # Server validation failed
            error_msg = server_result.get("error", "Server validation failed")
            job.status = ValidationStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.error_message = error_msg
            db.commit()
            service.close()
            logger.error(f"Server validation failed: {error_msg}")
            return server_result
        
        # Both validations completed successfully
        job.status = ValidationStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        db.commit()
        service.close()
        
        result = {
            "success": True,
            "landing_zone": lz_result,
            "servers": server_result
        }
        
        logger.info(f"Validation job {job_id} completed successfully")
        return result
        
    except Exception as e:
        logger.exception(f"Validation job {job_id} failed with exception")
        
        # Update job status to failed
        job = db.query(ValidationJob).filter(ValidationJob.id == job_id).first()
        if job:
            job.status = ValidationStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.error_message = str(e)
            db.commit()
        
        return {"success": False, "error": str(e)}
    
    finally:
        db.close()



@celery_app.task(name="workers.tasks.cleanup_old_jobs")
def cleanup_old_jobs():
    """
    Periodic task to clean up old validation jobs.
    
    This can be scheduled via Celery Beat if needed.
    """
    db = SessionLocal()
    try:
        # Example: Delete jobs older than 90 days
        # from datetime import timedelta
        # cutoff_date = datetime.utcnow() - timedelta(days=90)
        # db.query(ValidationJob).filter(
        #     ValidationJob.created_at < cutoff_date
        # ).delete()
        # db.commit()
        logger.info("Cleanup task executed (not implemented)")
    finally:
        db.close()
