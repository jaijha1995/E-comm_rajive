# tasks.py
import logging
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_welcome_email(self, email, context):
    try:
        subject = context.get("subject", "Welcome to GXI Network")
        html_message = render_to_string("welcome_email_template.html", context)
        plain_message = render_to_string("welcome.txt", context)

        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")

        send_mail(
            subject,
            plain_message,
            from_email,
            [email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info("Welcome email queued/sent to %s", email)
        return {"status": "sent", "to": email}

    except Exception as exc:
        logger.exception("Failed to send welcome email to %s: %s", email, exc)
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            logger.error("Max retries exceeded for sending welcome email to %s", email)
            return {"status": "failed", "to": email, "error": str(exc)}
