import logging
from config import settings

logger = logging.getLogger(__name__)


async def send_alert_email(transaction_id: str, amount: float, risk_score: float, merchant: str):
    """Send fraud alert email. Logs if SMTP not configured."""
    subject = f"🚨 RetailGuard Fraud Alert — Transaction {transaction_id[:8]}"
    body = f"""
RetailGuard has detected a potentially fraudulent transaction.

Transaction ID : {transaction_id}
Amount         : ${amount:,.2f}
Risk Score     : {risk_score:.2%}
Merchant       : {merchant}

Please log in to RetailGuard to review and investigate this alert.

— RetailGuard Automated Alert System
"""
    if not settings.SMTP_HOST or settings.SMTP_HOST == "smtp.example.com":
        logger.info(f"[EMAIL MOCK] To: {settings.ALERT_EMAIL}\nSubject: {subject}\n{body}")
        return

    try:
        import aiosmtplib
        from email.message import EmailMessage
        msg = EmailMessage()
        msg["From"] = settings.SMTP_USER
        msg["To"] = settings.ALERT_EMAIL
        msg["Subject"] = subject
        msg.set_content(body)
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
        logger.info(f"Alert email sent for transaction {transaction_id}")
    except Exception as e:
        logger.error(f"Email delivery failed for {transaction_id}: {e}")
