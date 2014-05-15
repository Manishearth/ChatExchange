import httmock

from chatexchange import Browser

from mock_responses import (
    only_httmock, favorite_with_test_fkey, TEST_FKEY)


def test_update_fkey():
    """
    Tests that the correct chat fkey is retrived, using a mock response
    with a copy of a real response from /chats/join/favorite
    """
    with only_httmock(favorite_with_test_fkey):
        browser = Browser()
        browser.host = 'stackexchange.com'

        assert browser.chat_fkey == TEST_FKEY


def test_user_agent():
    """
    Tests that HTTP requests made from a Browser use the intended
    User-Agent.

    WebSocket connections are not tested.
    """
    good_requests = []

    @httmock.all_requests
    def verify_user_agent(url, request):
        assert request.headers['user-agent'] == Browser.user_agent
        good_requests.append(request)
        return '<!doctype html><html><head><title>Hello<body>World'

    with only_httmock(verify_user_agent):
        browser = Browser()

        browser.get_soup('http://example.com/', with_chat_root=False)
        browser.get_soup('http://example.com/2', with_chat_root=False)

        assert len(good_requests) == 2, "Unexpected number of requests"
