import chatexchange

import live_testing


if live_testing.enabled:
    def test_user_info():
        client = chatexchange.Client('stackexchange.com')

        user = client.get_user(-2)
        assert user.id == -2
        assert not user.is_moderator
        assert user.name == "Stack Exchange"
        assert user.room_count >= 18
        assert user.message_count >= 129814
