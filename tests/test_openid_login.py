import time

import pytest

from chatexchange.browser import Browser, LoginError

from tests import live_testing


if live_testing.enabled:

    @pytest.mark.timeout(240)
    def test_openid_login():
        """
        Tests that login works.
        """
        browser = Browser()

        # avoid hitting the SE servers too frequently
        time.sleep(2)

        browser.login_se_openid(
            live_testing.email,
            live_testing.password)


    @pytest.mark.timeout(240)
    def test_openid_login_recognizes_failure():
        """
        Tests that failed SE OpenID logins raise errors.
        """
        browser = Browser()

        # avoid hitting the SE servers too frequently
        time.sleep(2)

        with pytest.raises(LoginError):
            invalid_password = 'no' + 't' * len(live_testing.password)

            browser.login_se_openid(
                live_testing.email,
                invalid_password)
