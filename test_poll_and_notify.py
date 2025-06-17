import unittest
from unittest.mock import patch, MagicMock
from poll_and_notify import EndpointPoller

class TestEndpointPoller(unittest.TestCase):
    def setUp(self):
        self.poller = EndpointPoller(
            endpoint_url="https://test.com",
            gmail_user="test@gmail.com",
            gmail_password="test_password",
            recipient_email="recipient@test.com",
            poll_interval=1
        )

    @patch('requests.get')
    def test_poll_endpoint_with_data(self, mock_get):
        # Mock a successful response with data
        mock_response = MagicMock()
        mock_response.content = b'{"key": "value"}'
        mock_response.json.return_value = {"key": "value"}
        mock_get.return_value = mock_response

        result = self.poller.poll_endpoint()
        self.assertEqual(result, {"key": "value"})

    @patch('requests.get')
    def test_poll_endpoint_with_empty_data(self, mock_get):
        # Mock a successful response with empty data
        mock_response = MagicMock()
        mock_response.content = b''
        mock_get.return_value = mock_response

        result = self.poller.poll_endpoint()
        self.assertIsNone(result)

    @patch('requests.get')
    def test_poll_endpoint_with_error(self, mock_get):
        # Mock a failed request
        mock_get.side_effect = Exception("Connection error")
        
        result = self.poller.poll_endpoint()
        self.assertIsNone(result)

    @patch('smtplib.SMTP_SSL')
    def test_send_email_success(self, mock_smtp):
        # Mock successful email sending
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = self.poller.send_email("Test Subject", "Test Body")
        self.assertTrue(result)
        mock_server.login.assert_called_once()
        mock_server.send_message.assert_called_once()

    @patch('smtplib.SMTP_SSL')
    def test_send_email_failure(self, mock_smtp):
        # Mock failed email sending
        mock_smtp.side_effect = Exception("SMTP error")

        result = self.poller.send_email("Test Subject", "Test Body")
        self.assertFalse(result)

    @patch('poll_and_notify.EndpointPoller.poll_endpoint')
    @patch('poll_and_notify.EndpointPoller.send_email')
    def test_start_polling(self, mock_send_email, mock_poll_endpoint):
        # Mock the polling sequence
        mock_poll_endpoint.side_effect = [
            None,  # First poll returns None
            {"data": "test"},  # Second poll returns data
        ]
        mock_send_email.return_value = True

        # We need to limit the polling to avoid infinite loop
        with patch('time.sleep', side_effect=StopIteration):
            try:
                self.poller.start_polling()
            except StopIteration:
                pass

        self.assertEqual(mock_poll_endpoint.call_count, 2)
        mock_send_email.assert_called_once()

if __name__ == '__main__':
    unittest.main() 