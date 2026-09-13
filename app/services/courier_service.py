import os
import re
import logging
import asyncio
from typing import Dict, Any, Optional, List
from courier.client import Courier

logger = logging.getLogger("skincare_api")


def _mask_email(email: str) -> str:
    """Masks an email for privacy-safe logging (e.g. j***n@example.com)."""
    if not email or "@" not in email:
        return "[INVALID_EMAIL]"
    parts = email.split("@", 1)
    user, domain = parts[0], parts[1]
    if len(user) <= 2:
        masked_user = user[0] + "*"
    else:
        masked_user = user[0] + "*" * (len(user) - 2) + user[-1]
    return f"{masked_user}@{domain}"


def get_courier_client() -> Courier:
    """
    Initializes and returns the official Courier SDK client.
    Reads the API key strictly from the COURIER_API_KEY environment variable.
    """
    api_key = os.environ.get("COURIER_API_KEY", "").strip()
    if not api_key or api_key == "replace_with_your_new_courier_api_key":
        raise ValueError(
            "COURIER_API_KEY environment variable is missing or unconfigured. "
            "Please configure your active Courier API key in your .env file."
        )
    return Courier(api_key=os.environ["COURIER_API_KEY"])


def send_email_notification(
    recipient_email: str,
    subject: str,
    html_content: str,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Sends a transactional email notification directly to a recipient email
    using the official Courier Python SDK. Delivery is routed through the
    connected Gmail integration configured in the Courier dashboard.

    Parameters:
        recipient_email: Destination email address (e.g. user.email or patient.email).
        subject: Generic, privacy-safe subject line (no sensitive health data).
        html_content: Responsive HTML markup for the notification body.
        user_id: Optional project user or patient identifier.

    Returns:
        Dict containing success status, Courier request_id, masked recipient,
        and human-readable status message.
    """
    clean_recipient = (recipient_email or "").strip().lower()
    if not clean_recipient or "@" not in clean_recipient:
        error_msg = f"Invalid email recipient provided: {clean_recipient}"
        logger.warning(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "recipient": clean_recipient,
            "request_id": None
        }

    # Sanitize subject to ensure medical details/prescriptions are never in subjects
    clean_subject = (subject or "Update from AI Skin Intelligence").strip()

    masked_recipient = _mask_email(clean_recipient)
    logger.info("Initiating Courier email dispatch to recipient: %s | Subject: '%s'", masked_recipient, clean_subject)

    try:
        client = get_courier_client()

        to_payload: Dict[str, Any] = {
            "email": clean_recipient
        }
        if user_id:
            to_payload["user_id"] = str(user_id)

        # Courier direct email recipient format
        response = client.send.message(
            message={
                "to": to_payload,
                "content": {
                    "version": "2022-01-01",
                    "elements": [
                        {
                            "type": "meta",
                            "title": clean_subject
                        },
                        {
                            "type": "html",
                            "content": html_content
                        }
                    ]
                }
            }
        )

        request_id = getattr(response, "request_id", None) or (response.get("request_id") if isinstance(response, dict) else str(response))
        logger.info(
            "Courier email dispatched successfully. Request ID: %s | Recipient: %s",
            request_id, masked_recipient
        )

        return {
            "success": True,
            "request_id": request_id,
            "recipient": clean_recipient,
            "subject": clean_subject,
            "message": f"Notification successfully submitted to Courier (Request ID: {request_id})."
        }

    except ValueError as val_err:
        logger.error("Courier configuration error: %s", val_err)
        return {
            "success": False,
            "error": str(val_err),
            "recipient": clean_recipient,
            "request_id": None,
            "message": f"Courier configuration error: {val_err}"
        }
    except Exception as exc:
        logger.error("Courier API dispatch failed for %s: %s", masked_recipient, exc)
        return {
            "success": False,
            "error": str(exc),
            "recipient": clean_recipient,
            "request_id": None,
            "message": f"Courier dispatch failed: {exc}"
        }


async def send_email_notification_async(
    recipient_email: str,
    subject: str,
    html_content: str,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Non-blocking asynchronous wrapper around send_email_notification.
    Executes the Courier HTTP network call in a worker thread so the
    FastAPI event loop remains responsive.
    """
    return await asyncio.to_thread(
        send_email_notification,
        recipient_email=recipient_email,
        subject=subject,
        html_content=html_content,
        user_id=user_id
    )


def get_courier_delivery_status(request_id: str) -> Dict[str, Any]:
    """
    Retrieves message delivery status from Courier using its request ID.
    Inspects provider information to verify delivery through the connected
    Gmail integration.

    Returns:
        Dict containing:
            - request_id: Courier request / message ID
            - status: Overall delivery status (e.g. DELIVERED, SENT, ENQUEUED, UNDELIVERABLE)
            - provider: Name of the delivery provider (expected: 'gmail')
            - provider_error: Any provider-specific error message
            - delivered: Delivery timestamp (if available)
            - raw: Structured details
    """
    clean_id = (request_id or "").strip()
    if not clean_id:
        return {
            "success": False,
            "error": "request_id is required to fetch delivery status.",
            "status": "UNKNOWN",
            "provider": None,
            "provider_error": None
        }

    try:
        client = get_courier_client()
        msg = client.messages.retrieve(message_id=clean_id)

        overall_status = getattr(msg, "status", None) or "UNKNOWN"
        providers_list = getattr(msg, "providers", None) or []
        provider_name = None
        provider_error = None

        if isinstance(providers_list, list) and len(providers_list) > 0:
            primary_p = providers_list[0]
            if isinstance(primary_p, dict):
                provider_name = primary_p.get("provider") or primary_p.get("channel")
                provider_error = primary_p.get("error")
            else:
                provider_name = getattr(primary_p, "provider", None) or getattr(primary_p, "channel", None)
                provider_error = getattr(primary_p, "error", None)

        # Top-level fallback error
        if not provider_error and getattr(msg, "error", None):
            provider_error = getattr(msg, "error", None)

        logger.info(
            "Courier status retrieved for Request ID %s | Status: %s | Provider: %s",
            clean_id, overall_status, provider_name
        )

        return {
            "success": True,
            "request_id": clean_id,
            "status": str(overall_status).upper(),
            "provider": provider_name,
            "provider_error": provider_error,
            "delivered": getattr(msg, "delivered", None),
            "sent": getattr(msg, "sent", None)
        }

    except Exception as exc:
        logger.error("Failed to retrieve Courier status for Request ID %s: %s", clean_id, exc)
        return {
            "success": False,
            "request_id": clean_id,
            "error": str(exc),
            "status": "ERROR",
            "provider": None,
            "provider_error": str(exc)
        }
