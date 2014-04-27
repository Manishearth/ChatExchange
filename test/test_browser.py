from chatexchange.browser import SEChatBrowser

from .mock_responses import (
    only_httmock, favorite_with_test_fkey, TEST_FKEY)


def test_update_fkey():
    """
    Tests that the correct fkey is retrived, using a mock response with
    a copy of a real response from /chats/join/favorite
    """
    with only_httmock(favorite_with_test_fkey):
        browser = SEChatBrowser()
        browser.chatroot = "http://chat.stackexchange.com"

        assert browser.updateFkey(), "fkey update failed"

        assert browser.chatfkey == TEST_FKEY
