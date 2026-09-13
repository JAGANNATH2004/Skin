import unittest
from unittest.mock import patch, MagicMock
import os

from app.services.courier_service import (
    _mask_email,
    send_email_notification,
    get_courier_delivery_status
)
from app.services.notification_service import (
    generate_routine_reminder,
    generate_replenishment_reminder,
    send_welcome_notification,
    send_appointment_reminder,
    send_password_reset_notification,
    send_clinical_update_notification,
    is_courier_configured
)


class TestCourierService(unittest.TestCase):
    def test_mask_email(self):
        self.assertEqual(_mask_email('user@example.com'), 'u**r@example.com')
        self.assertEqual(_mask_email('ab@test.com'), 'a*@test.com')
        self.assertEqual(_mask_email('invalid'), '[INVALID_EMAIL]')

    @patch('app.services.courier_service.Courier')
    @patch.dict(os.environ, {'COURIER_API_KEY': 'test_courier_key_12345'})
    def test_send_email_notification_direct_format(self, mock_courier_cls):
        mock_client = MagicMock()
        mock_courier_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.request_id = 'req-1234-abcd'
        mock_client.send.message.return_value = mock_response

        res = send_email_notification(
            recipient_email='patient@example.com',
            subject='AI Skin Intelligence: Morning Routine Reminder',
            html_content='<p>Hello test</p>',
            user_id='42'
        )

        self.assertTrue(res['success'])
        self.assertEqual(res['request_id'], 'req-1234-abcd')
        self.assertEqual(res['recipient'], 'patient@example.com')

        # Verify Courier client initialization
        mock_courier_cls.assert_called_once_with(api_key='test_courier_key_12345')

        # Verify direct message recipient format
        mock_client.send.message.assert_called_once()
        call_kwargs = mock_client.send.message.call_args[1]
        msg = call_kwargs['message']
        self.assertEqual(msg['to']['email'], 'patient@example.com')
        self.assertEqual(msg['to']['user_id'], '42')
        self.assertEqual(msg['content']['version'], '2022-01-01')
        self.assertEqual(msg['content']['elements'][0]['type'], 'meta')
        self.assertEqual(msg['content']['elements'][0]['title'], 'AI Skin Intelligence: Morning Routine Reminder')
        self.assertEqual(msg['content']['elements'][1]['type'], 'html')
        self.assertEqual(msg['content']['elements'][1]['content'], '<p>Hello test</p>')

    @patch.dict(os.environ, {'COURIER_API_KEY': 'replace_with_your_new_courier_api_key'})
    def test_send_email_unconfigured_key(self):
        res = send_email_notification(
            recipient_email='test@example.com',
            subject='Test',
            html_content='<p>Test</p>'
        )
        self.assertFalse(res['success'])
        self.assertIn('missing or unconfigured', res['error'])

    def test_send_email_invalid_recipient(self):
        res = send_email_notification(
            recipient_email='not_an_email',
            subject='Test',
            html_content='<p>Test</p>'
        )
        self.assertFalse(res['success'])
        self.assertIn('Invalid email recipient', res['error'])

    @patch('app.services.courier_service.Courier')
    @patch.dict(os.environ, {'COURIER_API_KEY': 'test_key'})
    def test_get_courier_delivery_status_gmail_provider(self, mock_courier_cls):
        mock_client = MagicMock()
        mock_courier_cls.return_value = mock_client

        mock_msg = MagicMock()
        mock_msg.status = 'DELIVERED'
        mock_msg.error = None
        mock_msg.providers = [
            {'channel': 'email', 'provider': 'gmail', 'status': 'DELIVERED', 'error': None}
        ]
        mock_msg.delivered = 1710000000
        mock_msg.sent = 1709999900
        mock_client.messages.retrieve.return_value = mock_msg

        status_res = get_courier_delivery_status('req-1234-abcd')

        self.assertTrue(status_res['success'])
        self.assertEqual(status_res['status'], 'DELIVERED')
        self.assertEqual(status_res['provider'], 'gmail')
        self.assertIsNone(status_res['provider_error'])
        mock_client.messages.retrieve.assert_called_once_with(message_id='req-1234-abcd')

    def test_template_subjects_are_privacy_safe(self):
        routine = generate_routine_reminder('Jane', 'Morning missed', 'morning')
        self.assertNotIn('acne', routine['subject'].lower())
        self.assertIn('AI Skin Intelligence', routine['subject'])

        replenish = generate_replenishment_reminder('Jane', '30 days')
        self.assertEqual(replenish['subject'], 'AI Skin Intelligence: Product Replenishment Advisory')

    @patch('app.services.notification_service.send_email_notification')
    def test_dedicated_trigger_helpers(self, mock_send):
        mock_send.return_value = {'success': True, 'request_id': 'req-welcome'}
        res = send_welcome_notification('user@example.com', 'Alice', user_id='1')
        self.assertTrue(res['success'])
        mock_send.assert_called_once()
        self.assertEqual(mock_send.call_args[1]['recipient_email'], 'user@example.com')


if __name__ == '__main__':
    unittest.main()
