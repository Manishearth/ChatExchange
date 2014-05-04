import time

import pytest

from chatexchange.browser import SEChatBrowser, LoginError

import live_testing


if live_testing.enabled:
    def test_openid_login_recognizes_failure():
        """
        Tests that failed SE OpenID logins raise errors.
        """
        browser = SEChatBrowser()

        # avoid hitting the SE servers too frequently
        time.sleep(2)

        with pytest.raises(LoginError):
            invalid_password = 'no' + 't' * len(live_testing.password)

            browser.loginSEOpenID(
                live_testing.username,
                invalid_password)
