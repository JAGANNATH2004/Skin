import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from app.services.courier_service import send_email_notification, send_email_notification_async

load_dotenv()

logger = logging.getLogger("skincare_api")


def is_courier_configured() -> bool:
    """Returns True if COURIER_API_KEY is configured in the environment."""
    key = (os.getenv("COURIER_API_KEY") or "").strip()
    return bool(key and key != "replace_with_your_new_courier_api_key")



def create_base_email_template(
    title: str,
    badge: str,
    content_html: str,
    action_button_text: str = "Open My Dashboard",
    action_url: str = "http://127.0.0.1:8000/user/user.html#score",
    footer_note: str = "You received this automated reminder based on your skincare performance and profile preferences."
) -> str:
    """
    Renders an elegant, modern, responsive HTML email template
    with dark-slate header, vibrant accent cards, and actionable CTA.
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    body {{
      margin: 0;
      padding: 0;
      background-color: #f1f5f9;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      color: #1e293b;
      -webkit-font-smoothing: antialiased;
    }}
    .email-container {{
      max-width: 600px;
      margin: 30px auto;
      background: #ffffff;
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.05);
      border: 1px solid #e2e8f0;
    }}
    .email-header {{
      background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
      padding: 32px 28px;
      text-align: center;
      color: #ffffff;
    }}
    .brand-title {{
      font-size: 13px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: #38bdf8;
      margin-bottom: 6px;
    }}
    .email-title {{
      font-size: 22px;
      font-weight: 800;
      margin: 0 0 10px 0;
      color: #f8fafc;
      letter-spacing: -0.02em;
    }}
    .badge {{
      display: inline-block;
      padding: 4px 12px;
      background: rgba(56, 189, 248, 0.15);
      border: 1px solid rgba(56, 189, 248, 0.3);
      color: #7dd3fc;
      border-radius: 20px;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .email-body {{
      padding: 32px 28px;
      line-height: 1.65;
      font-size: 15px;
      color: #334155;
    }}
    .highlight-card {{
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-left: 4px solid #6366f1;
      border-radius: 12px;
      padding: 18px 20px;
      margin: 20px 0;
    }}
    .cta-container {{
      text-align: center;
      margin: 32px 0 16px 0;
    }}
    .cta-btn {{
      display: inline-block;
      background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%);
      color: #ffffff !important;
      text-decoration: none;
      padding: 12px 30px;
      border-radius: 30px;
      font-weight: 700;
      font-size: 14px;
      box-shadow: 0 4px 14px rgba(79, 70, 229, 0.3);
    }}
    .email-footer {{
      background: #f8fafc;
      padding: 20px 28px;
      border-top: 1px solid #e2e8f0;
      text-align: center;
      font-size: 12px;
      color: #64748b;
      line-height: 1.5;
    }}
    .email-footer a {{
      color: #6366f1;
      text-decoration: none;
    }}
  </style>
</head>
<body>
  <div class="email-container">
    <div class="email-header">
      <div class="brand-title">AI Skin Intelligence &bull; Reminders</div>
      <h1 class="email-title">{title}</h1>
      <span class="badge">{badge}</span>
    </div>
    <div class="email-body">
      {content_html}
      <div class="cta-container">
        <a href="{action_url}" class="cta-btn">{action_button_text} &rarr;</a>
      </div>
    </div>
    <div class="email-footer">
      <p style="margin: 0 0 6px 0;">{footer_note}</p>
      <p style="margin: 0;">You can update your email reminder preferences anytime in your <a href="{action_url}">Account Profile</a>.</p>
    </div>
  </div>
</body>
</html>"""


def send_raw_email(recipient: str, subject: str, html_content: str, plain_text: Optional[str] = None) -> Dict[str, Any]:
    """
    Routes email delivery through the official Courier Python SDK with Gmail integration.
    Maintained for backwards-compatibility.
    """
    return send_email_notification(
        recipient_email=recipient,
        subject=subject,
        html_content=html_content
    )



# ---------------------------------------------------------------------------
# Template Generators for the 6 Reminder Categories
# ---------------------------------------------------------------------------

def generate_routine_reminder(user_name: str, trigger_reason: str, time_of_day: str = "morning") -> Dict[str, str]:
    if time_of_day.lower() == "evening":
        subject = "AI Skin Intelligence: Evening Routine Reminder"
        title = "Complete Your Evening Skincare Regimen"
        badge = "Evening Routine Alert"
        body = f"""
        <p>Hello <strong>{user_name}</strong>,</p>
        <p>Your performance check indicates your evening skincare routine has not yet been logged today.</p>
        <div class="highlight-card">
          <strong style="color: #4338ca;">Why Consistency Matters Tonight:</strong>
          <p style="margin: 6px 0 0 0; font-size: 14px;">
            While you sleep, skin blood flow increases and epidermal cell renewal peaks.
            Applying your hydrating cleanser, treatment actives, and moisture lock ensures optimal overnight barrier recovery.
          </p>
        </div>
        <p><strong>Status:</strong> {trigger_reason}</p>
        <p>Take 2 minutes to complete your steps and maintain your skincare streak!</p>
        """
    else:
        subject = "AI Skin Intelligence: Morning Routine Reminder"
        title = "Start Your Day With Targeted Skin Protection"
        badge = "Morning Routine Alert"
        body = f"""
        <p>Hello <strong>{user_name}</strong>,</p>
        <p>We noticed you haven't checked off your morning skincare regimen yet today.</p>
        <div class="highlight-card">
          <strong style="color: #4338ca;">Morning Regimen Focus:</strong>
          <p style="margin: 6px 0 0 0; font-size: 14px;">
            Morning routines shield your skin against environmental oxidants and UV exposure.
            Don't forget your antioxidant serum and broad-spectrum SPF 50+!
          </p>
        </div>
        <p><strong>Status:</strong> {trigger_reason}</p>
        <p>Check in now to keep your streak going and protect your skin barrier.</p>
        """
    html = create_base_email_template(
        title=title,
        badge=badge,
        content_html=body,
        action_button_text="Complete Routine Check-in"
    )
    return {"subject": subject, "html": html}


def generate_replenishment_reminder(user_name: str, trigger_reason: str, product_name: str = "Daily Essential Cleanser & SPF") -> Dict[str, str]:
    subject = "AI Skin Intelligence: Product Replenishment Advisory"
    title = "Time to Restock Your Skincare Regimen"
    badge = "Replenishment Advisory"
    body = f"""
    <p>Hello <strong>{user_name}</strong>,</p>
    <p>Based on your routine usage and consistency history, your daily essential products may be running low.</p>
    <div class="highlight-card">
      <strong style="color: #4338ca;">Replenishment Tracker:</strong>
      <p style="margin: 6px 0 0 0; font-size: 14px;">
        <strong>Item:</strong> {product_name}<br>
        <strong>Usage Duration:</strong> 30+ days of regular application.<br>
        <strong>Advice:</strong> Maintaining continuous supply prevents routine breaks, which can set back acne control and barrier strength.
      </p>
    </div>
    <p><strong>Performance Trigger:</strong> {trigger_reason}</p>
    <p>Review your product shelf and order a replacement in advance so your regimen remains seamless.</p>
    """
    html = create_base_email_template(
        title=title,
        badge=badge,
        content_html=body,
        action_button_text="View Routine Products"
    )
    return {"subject": subject, "html": html}


def generate_hydration_reminder(user_name: str, trigger_reason: str, target_water: str = "2.5 Liters") -> Dict[str, str]:
    subject = "AI Skin Intelligence: Hydration Reminder"
    title = "Hydrate for Healthy, Plump Skin"
    badge = "Hydration Performance"
    body = f"""
    <p>Hello <strong>{user_name}</strong>,</p>
    <p>Your skin health profile suggests that intracellular hydration could use a boost to maximize product efficacy.</p>
    <div class="highlight-card" style="border-left-color: #0284c7;">
      <strong style="color: #0369a1;">Hydration Benchmark:</strong>
      <p style="margin: 6px 0 0 0; font-size: 14px;">
        <strong>Daily Target:</strong> {target_water}<br>
        <strong>Skin Benefit:</strong> Water intake supports extracellular matrix turgor, improving elasticity and speeding up skin cellular turnover.
      </p>
    </div>
    <p><strong>Profile Indicator:</strong> {trigger_reason}</p>
    <p>Remember to drink a glass of water right now and keep your hydration bottle nearby!</p>
    """
    html = create_base_email_template(
        title=title,
        badge=badge,
        content_html=body,
        action_button_text="Update Hydration Log"
    )
    return {"subject": subject, "html": html}


def generate_sleep_reminder(user_name: str, trigger_reason: str, target_hours: str = "7-8 hours") -> Dict[str, str]:
    subject = "AI Skin Intelligence: Sleep & Recovery Reminder"
    title = "Skin Recovery Starts Tonight"
    badge = "Sleep & Recovery"
    body = f"""
    <p>Hello <strong>{user_name}</strong>,</p>
    <p>Our performance monitoring detected irregular sleep metrics or late check-in intervals in your skincare log.</p>
    <div class="highlight-card" style="border-left-color: #8b5cf6;">
      <strong style="color: #6d28d9;">Cellular Repair Science:</strong>
      <p style="margin: 6px 0 0 0; font-size: 14px;">
        During stage 3 slow-wave sleep, human growth hormone (HGH) accelerates skin cell repair and collagen synthesis.
        Chronic sleep deprivation spikes cortisol, leading to barrier disruption and increased inflammation.
      </p>
    </div>
    <p><strong>Target Rest:</strong> {target_hours} tonight.</p>
    <p><strong>Performance Trigger:</strong> {trigger_reason}</p>
    <p>Wind down 30 minutes before bed, complete your nighttime routine, and let your skin regenerate!</p>
    """
    html = create_base_email_template(
        title=title,
        badge=badge,
        content_html=body,
        action_button_text="View Evening Routine"
    )
    return {"subject": subject, "html": html}


def generate_progress_alert(user_name: str, trigger_reason: str, score_delta: Optional[str] = "+5 pts") -> Dict[str, str]:
    subject = "AI Skin Intelligence: Progress Update"
    title = "Your Skincare Journey Milestones"
    badge = "Progress Milestone"
    body = f"""
    <p>Hello <strong>{user_name}</strong>,</p>
    <p>Here is your latest skincare performance update based on your assessments and consistency.</p>
    <div class="highlight-card" style="border-left-color: #10b981;">
      <strong style="color: #047857;">Performance Milestone:</strong>
      <p style="margin: 6px 0 0 0; font-size: 14px;">
        <strong>Milestone:</strong> {trigger_reason}<br>
        <strong>Impact:</strong> Regular routine compliance is driving measurable improvements in your skin barrier resistance and tone uniformity.
      </p>
    </div>
    <p>Log into your portal to view your comprehensive score breakdown, comparison photos, and personalized tips.</p>
    """
    html = create_base_email_template(
        title=title,
        badge=badge,
        content_html=body,
        action_button_text="View Progress Analytics"
    )
    return {"subject": subject, "html": html}


def generate_platform_notification(user_name: str, trigger_reason: str, custom_message: Optional[str] = None) -> Dict[str, str]:
    subject = "Update from AI Skin Intelligence"
    title = "Important Platform & Regimen Update"
    badge = "Platform Advisory"
    msg = custom_message or "New seasonal routine adaptations and dermatological recommendations are ready for review in your account."
    body = f"""
    <p>Hello <strong>{user_name}</strong>,</p>
    <p>{msg}</p>
    <div class="highlight-card" style="border-left-color: #f59e0b;">
      <strong style="color: #b45309;">Notice Details:</strong>
      <p style="margin: 6px 0 0 0; font-size: 14px;">
        {trigger_reason}
      </p>
    </div>
    <p>Please log in to your portal to inspect the latest adjustments to your routine or consultant notes.</p>
    """
    html = create_base_email_template(
        title=title,
        badge=badge,
        content_html=body,
        action_button_text="Open User Portal"
    )
    return {"subject": subject, "html": html}


# ---------------------------------------------------------------------------
# Dedicated Trigger Helpers (Registration, Appointment, Reset, Clinical)
# ---------------------------------------------------------------------------

def send_welcome_notification(user_email: str, user_name: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """Dispatches a welcome and onboarding notification via Courier."""
    subject = "Welcome to AI Skin Intelligence"
    title = "Welcome to AI Skin Intelligence"
    badge = "Welcome"
    body = f"""
    <p>Hello <strong>{user_name}</strong>,</p>
    <p>Thank you for joining AI Skin Intelligence! Your account is active and ready to use.</p>
    <div class="highlight-card">
      <strong style="color: #4338ca;">Getting Started:</strong>
      <p style="margin: 6px 0 0 0; font-size: 14px;">
        1. Complete your baseline skin assessment.<br>
        2. Explore your personalized routine recommendations.<br>
        3. Track your daily skincare consistency and milestones.
      </p>
    </div>
    <p>We're thrilled to support you on your skincare journey.</p>
    """
    html = create_base_email_template(
        title=title,
        badge=badge,
        content_html=body,
        action_button_text="Open Dashboard",
        action_url="http://127.0.0.1:8000/user/user.html"
    )
    return send_email_notification(recipient_email=user_email, subject=subject, html_content=html, user_id=user_id)


def send_appointment_reminder(
    user_email: str,
    user_name: str,
    appointment_time: str,
    doctor_name: str = "Clinical Consultant",
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Dispatches an appointment or consultation reminder via Courier."""
    subject = "Appointment reminder from AI Skin Intelligence"
    title = "Upcoming Consultation Reminder"
    badge = "Consultation"
    body = f"""
    <p>Hello <strong>{user_name}</strong>,</p>
    <p>This is a reminder of your scheduled consultation session.</p>
    <div class="highlight-card" style="border-left-color: #3b82f6;">
      <strong style="color: #1d4ed8;">Session Details:</strong>
      <p style="margin: 6px 0 0 0; font-size: 14px;">
        <strong>Specialist:</strong> {doctor_name}<br>
        <strong>Scheduled Time:</strong> {appointment_time}<br>
        <strong>Format:</strong> Virtual Consultation
      </p>
    </div>
    <p>Please log in a few minutes prior to the session to review your latest notes.</p>
    """
    html = create_base_email_template(
        title=title,
        badge=badge,
        content_html=body,
        action_button_text="View Details",
        action_url="http://127.0.0.1:8000/user/user.html"
    )
    return send_email_notification(recipient_email=user_email, subject=subject, html_content=html, user_id=user_id)


def send_password_reset_notification(user_email: str, reset_link: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """Dispatches a secure password reset link via Courier."""
    subject = "Security update from AI Skin Intelligence"
    title = "Password Reset Request"
    badge = "Security"
    body = f"""
    <p>Hello,</p>
    <p>We received a request to reset your password for AI Skin Intelligence.</p>
    <div class="highlight-card" style="border-left-color: #ef4444;">
      <strong style="color: #b91c1c;">Security Notice:</strong>
      <p style="margin: 6px 0 0 0; font-size: 14px;">
        If you did not request this change, please ignore this message. The reset link will expire shortly.
      </p>
    </div>
    """
    html = create_base_email_template(
        title=title,
        badge=badge,
        content_html=body,
        action_button_text="Reset Password",
        action_url=reset_link
    )
    return send_email_notification(recipient_email=user_email, subject=subject, html_content=html, user_id=user_id)


def send_clinical_update_notification(
    patient_email: str,
    patient_name: str,
    update_title: str,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Dispatches a clinical care update notification to a patient via Courier."""
    subject = "Update from AI Skin Intelligence"
    title = "Clinical Regimen Update"
    badge = "Clinical Advisory"
    body = f"""
    <p>Hello <strong>{patient_name}</strong>,</p>
    <p>Your consulting dermatologist has updated your clinical care notes and recommendations.</p>
    <div class="highlight-card" style="border-left-color: #10b981;">
      <strong style="color: #047857;">Notice:</strong>
      <p style="margin: 6px 0 0 0; font-size: 14px;">
        {update_title}
      </p>
    </div>
    <p>Please log in to your patient portal to review your updated routine instructions.</p>
    """
    html = create_base_email_template(
        title=title,
        badge=badge,
        content_html=body,
        action_button_text="Inspect Portal",
        action_url="http://127.0.0.1:8000/user/user.html"
    )
    return send_email_notification(recipient_email=patient_email, subject=subject, html_content=html, user_id=user_id)


# ---------------------------------------------------------------------------
# Universal Dispatcher Function
# ---------------------------------------------------------------------------

def dispatch_user_reminder(
    user: Any,
    reminder_type: str,
    trigger_reason: str,
    extra_data: Optional[Dict[str, Any]] = None,
    db: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Dispatches an email reminder for the specified category if the user
    has email push notifications enabled, using the official Courier Python SDK.
    """
    # Enforce Rule: Send through email only when user enabled push notifications
    if not getattr(user, "push_notifications_email", True):
        logger.info(
            "User %s has disabled email notifications. Skipping reminder [%s].",
            user.email, reminder_type
        )
        return {
            "success": False,
            "skipped": True,
            "reason": "User has disabled email push notifications.",
            "recipient": user.email,
            "reminder_type": reminder_type,
        }

    user_name = getattr(user, "first_name", "") or getattr(user, "name", "") or "Valued Member"
    category = reminder_type.lower().strip()
    extra_data = extra_data or {}

    # Select appropriate template
    if category == "routine":
        time_of_day = extra_data.get("time_of_day", "morning")
        template_res = generate_routine_reminder(user_name, trigger_reason, time_of_day)
    elif category == "replenishment":
        product_name = extra_data.get("product_name", "Daily Cleanser & Broad Spectrum SPF")
        template_res = generate_replenishment_reminder(user_name, trigger_reason, product_name)
    elif category == "hydration":
        target = extra_data.get("target_water", "2.5 Liters")
        template_res = generate_hydration_reminder(user_name, trigger_reason, target)
    elif category == "sleep":
        target_hours = extra_data.get("target_hours", "7-8 hours")
        template_res = generate_sleep_reminder(user_name, trigger_reason, target_hours)
    elif category == "progress":
        delta = extra_data.get("score_delta", "+5 pts")
        template_res = generate_progress_alert(user_name, trigger_reason, delta)
    elif category == "platform":
        custom_msg = extra_data.get("message", None)
        template_res = generate_platform_notification(user_name, trigger_reason, custom_msg)
    else:
        template_res = generate_platform_notification(user_name, trigger_reason)

    subject = template_res["subject"]
    html = template_res["html"]

    recipient = (extra_data.get("recipient_email") or getattr(user, "email", "")).strip().lower()
    user_id_val = str(getattr(user, "id", "")) if getattr(user, "id", None) else None

    # Send through official Courier Python SDK (delivered via connected Gmail integration)
    result = send_email_notification(
        recipient_email=recipient,
        subject=subject,
        html_content=html,
        user_id=user_id_val
    )

    # Log in database if db session provided
    if db:
        try:
            from app.models import UserReminderLog
            log_status = "sent" if result.get("success") else "failed"
            courier_req_id = result.get("request_id")
            log_entry = UserReminderLog(
                user_id=user.id,
                reminder_type=category,
                performance_trigger=trigger_reason[:250],
                channel="email",
                subject=subject[:250],
                status=log_status,
                courier_request_id=courier_req_id,
                sent_at=datetime.now(timezone.utc)
            )
            db.add(log_entry)
            db.commit()
        except Exception as log_exc:
            logger.error("Error writing UserReminderLog: %s", log_exc)

    result["reminder_type"] = category
    result["trigger_reason"] = trigger_reason
    return result

