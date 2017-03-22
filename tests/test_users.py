import pytest

import chatexchange

from tests import live_testing


if live_testing.enabled:
    @pytest.mark.timeout(240)
    def test_user_info():
        client = chatexchange.Client('stackexchange.com')

        user = client.get_user(-2)
        assert user.id == -2
        assert not user.is_moderator
        assert user.name == "Feeds"
        assert user.room_count >= 18
        assert user.message_count >= 129810
        assert user.reputation == -1

        user = client.get_user(31768)
        assert user.id == 31768
        assert user.is_moderator
        assert user.name == "ManishEarth"
        assert user.room_count >= 222
        assert user.message_count >= 89093
        assert user.reputation > 115000

        user = client.get_user(-5)
        assert user.id == -5
        assert not user.is_moderator
        assert user.last_seen == -1
        assert user.reputation == -1
