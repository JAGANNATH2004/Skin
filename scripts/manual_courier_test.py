import os
import sys
import time
import argparse
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
load_dotenv(ROOT_DIR / '.env')

from app.services.courier_service import send_email_notification, get_courier_delivery_status


def main():
    parser = argparse.ArgumentParser(
        description='Send a safe manual test email via Courier + Gmail integration.'
    )
    parser.add_argument(
        '--recipient',
        type=str,
        help='Destination test email address (e.g. your personal email for verification)'
    )
    args = parser.parse_args()

    api_key = (os.getenv('COURIER_API_KEY') or '').strip()
    if not api_key or api_key == 'replace_with_your_new_courier_api_key':
        print('=' * 60)
        print('ERROR: COURIER_API_KEY is not configured in .env!')
        print('Please generate a new API key in:')
        print('  Courier Dashboard -> Platform -> API Keys')
        print('And set in your .env:')
        print('  COURIER_API_KEY=your_new_courier_api_key_here')
        print('=' * 60)
        sys.exit(1)

    recipient = args.recipient
    if not recipient:
        try:
            recipient = input('Enter destination email for test notification: ').strip()
        except (EOFError, KeyboardInterrupt):
            print('\nCancelled.')
            sys.exit(0)

    if not recipient or '@' not in recipient:
        print('Error: A valid destination email is required.')
        sys.exit(1)

    subject = 'Update from AI Skin Intelligence'
    html_content = """<div style="font-family: sans-serif; max-width: 580px; margin: 20px auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 12px; background: #ffffff;">
  <h2 style="color: #0f172a; margin: 0 0 12px 0;">AI Skin Intelligence Notification Test</h2>
  <p style="color: #334155; font-size: 15px; line-height: 1.6;">This is a verification email from AI Skin Intelligence.</p>
  <div style="background: #f8fafc; border-left: 4px solid #6366f1; padding: 14px 18px; margin: 18px 0; border-radius: 8px;">
    <strong style="color: #4338ca;">Integration Status:</strong>
    <p style="margin: 6px 0 0 0; font-size: 14px; color: #334155;">Dispatched via Courier SDK and routed through your connected Gmail integration.</p>
  </div>
  <p style="color: #64748b; font-size: 12px; margin-top: 24px;">Courier delivery confirmation test.</p>
</div>"""

    print('=' * 60)
    print(f'Sending manual test notification to: {recipient}')
    print(f'Subject: {subject}')
    print('=' * 60)

    res = send_email_notification(
        recipient_email=recipient,
        subject=subject,
        html_content=html_content
    )

    if not res.get('success'):
        print(f"FAILED: {res.get('error') or res.get('message')}")
        sys.exit(1)

    request_id = res['request_id']
    print('SUCCESS: Notification submitted to Courier!')
    print(f"  Courier Request ID: {request_id}")
    print(f"  Recipient:          {res['recipient']}")
    print('')
    print('Checking message delivery status (waiting 3 seconds)...')
    time.sleep(3)

    status_res = get_courier_delivery_status(request_id)
    print('=' * 60)
    print('COURIER DELIVERY STATUS:')
    print(f"  Request ID:     {status_res.get('request_id')}")
    print(f"  Overall Status: {status_res.get('status')}")
    print(f"  Provider:       {status_res.get('provider')}")
    print(f"  Provider Error: {status_res.get('provider_error') or 'None'}")
    print('=' * 60)

    if status_res.get('provider') == 'gmail':
        print('[CONFIRMED] Email is routed through connected Gmail integration (provider: gmail)!')
    elif status_res.get('provider') == 'courier-email':
        print('[ACTION NEEDED] Provider is courier-email.')
        print('To route through Gmail:')
        print('  1. Go to Courier Dashboard -> Channels -> Email')
        print('  2. Prioritize your connected Gmail provider above courier-email')
        print('  3. Re-run this test to confirm provider: gmail')
    else:
        print(f"Provider reported: {status_res.get('provider') or 'Pending delivery / enqueued'}")
        print('Check Courier Dashboard -> Messages -> Log for final delivery confirmation.')


if __name__ == '__main__':
    main()