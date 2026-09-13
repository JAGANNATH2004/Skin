import os
import logging
import asyncio
from typing import Dict, Any, Optional
import requests

logger = logging.getLogger("skincare_api")

COURIER_API_BASE_URL = "https://api.courier.com"


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


def get_courier_api_key() -> str:
    """
    Reads the Courier API key strictly from the COURIER_API_KEY environment variable.
    Raises ValueError if the key is missing or unconfigured.
    """
    key = os.environ.get("COURIER_API_KEY", "").strip()
    if not key or key == "replace_with_your_new_courier_api_key":
        raise ValueError(
            "COURIER_API_KEY environment variable is missing or unconfigured. "
            "Please configure your active Courier API key in your .env or Render dashboard."
        )
    return key


def send_email_notification(
    recipient_email: str,
    subject: str,
    html_content: str,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Sends a transactional email notification directly to a recipient email
    using Courier's REST API. Delivery is routed through the connected
    Gmail integration configured in the Courier dashboard.

    Compatible with Render and FastAPI without relying on fragile SDK packages.
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

    clean_subject = (subject or "Update from AI Skin Intelligence").strip()
    masked_recipient = _mask_email(clean_recipient)
    logger.info("Initiating Courier email dispatch to: %s | Subject: '%s'", masked_recipient, clean_subject)

    try:
        api_key = get_courier_api_key()
    except ValueError as val_err:
        logger.error("Courier configuration error: %s", val_err)
        return {
            "success": False,
            "error": str(val_err),
            "recipient": clean_recipient,
            "request_id": None,
            "message": f"Courier configuration error: {val_err}"
        }

    # Prepare recipient payload
    to_payload: Dict[str, Any] = {"email": clean_recipient}
    if user_id:
        to_payload["user_id"] = str(user_id)

    # Standard Courier direct message format
    payload = {
        "message": {
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
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "AISkinIntelligence/2.0 (Python/Requests)"
    }

    try:
        # Timeout: 5 seconds connect, 15 seconds read
        response = requests.post(
            f"{COURIER_API_BASE_URL}/send",
            json=payload,
            headers=headers,
            timeout=(5.0, 15.0)
        )

        resp_data = response.json() if response.content else {}

        if response.status_code in (200, 201, 202):
            request_id = resp_data.get("requestId") or resp_data.get("request_id") or "SUBMITTED"
            logger.info("Courier email dispatched successfully. Request ID: %s | Recipient: %s", request_id, masked_recipient)
            return {
                "success": True,
                "request_id": request_id,
                "recipient": clean_recipient,
                "subject": clean_subject,
                "message": f"Notification successfully submitted to Courier (Request ID: {request_id})."
            }
        else:
            api_error_msg = resp_data.get("message") or resp_data.get("error") or f"HTTP {response.status_code}"
            logger.error("Courier API returned error status %s: %s", response.status_code, api_error_msg)
            return {
                "success": False,
                "error": str(api_error_msg),
                "status_code": response.status_code,
                "recipient": clean_recipient,
                "request_id": None,
                "message": f"Courier dispatch failed with status {response.status_code}: {api_error_msg}"
            }

    except requests.exceptions.Timeout:
        logger.error("Courier API request timed out for %s", masked_recipient)
        return {
            "success": False,
            "error": "Courier API request timed out",
            "recipient": clean_recipient,
            "request_id": None,
            "message": "Courier API connection timed out. Please try again."
        }
    except requests.exceptions.RequestException as req_err:
        logger.error("Network error communicating with Courier API for %s: %s", masked_recipient, req_err)
        return {
            "success": False,
            "error": str(req_err),
            "recipient": clean_recipient,
            "request_id": None,
            "message": f"Courier network connection error: {req_err}"
        }
    except Exception as exc:
        logger.error("Unexpected error during Courier dispatch for %s: %s", masked_recipient, exc)
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
    FastAPI event loop remains fully responsive.
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
        api_key = get_courier_api_key()
    except ValueError as val_err:
        return {
            "success": False,
            "request_id": clean_id,
            "error": str(val_err),
            "status": "UNCONFIGURED",
            "provider": None,
            "provider_error": str(val_err)
        }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(
            f"{COURIER_API_BASE_URL}/messages/{clean_id}",
            headers=headers,
            timeout=(5.0, 15.0)
        )
        if response.status_code != 200:
            return {
                "success": False,
                "request_id": clean_id,
                "error": f"Courier API returned status {response.status_code}",
                "status": "NOT_FOUND" if response.status_code == 404 else "ERROR",
                "provider": None,
                "provider_error": response.text[:200]
            }

        data = response.json()
        overall_status = data.get("status") or "UNKNOWN"
        providers_list = data.get("providers") or []
        provider_name = None
        provider_error = None

        if isinstance(providers_list, list) and len(providers_list) > 0:
            primary_p = providers_list[0]
            if isinstance(primary_p, dict):
                provider_name = primary_p.get("provider") or primary_p.get("channel")
                provider_error = primary_p.get("error")

        if not provider_error and data.get("error"):
            provider_error = data.get("error")

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
            "delivered": data.get("delivered"),
            "sent": data.get("sent")
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