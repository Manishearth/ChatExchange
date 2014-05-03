import httmock

from chatexchange.browser import SEChatBrowser

from mock_responses import (
    only_httmock, favorite_with_test_fkey, TEST_FKEY)


def test_update_fkey():
    """
    Tests that the correct chat fkey is retrived, using a mock response
    with a copy of a real response from /chats/join/favorite
    """
    with only_httmock(favorite_with_test_fkey):
        browser = SEChatBrowser()
        browser.host = 'stackexchange.com'

        assert browser.chat_fkey() == TEST_FKEY


def test_user_agent():
    """
    Tests that HTTP requests made from a SEChatBrowser use the intended
    User-Agent.

    WebSocket connections are not tested.
    """
    good_requests = []

    @httmock.all_requests
    def verify_user_agent(url, request):
        assert request.headers['user-agent'] == SEChatBrowser.user_agent
        good_requests.append(request)
        return '<!doctype html><html><head><title>Hello<body>World'

    with only_httmock(verify_user_agent):
        browser = SEChatBrowser()

        browser.getSomething('http://example.com/')
        browser.getSoup('http://example.com/')

        assert len(good_requests) == 2, "Unexpected number of requests"
