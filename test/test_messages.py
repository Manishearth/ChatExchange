import logging

from chatexchange import events, wrapper

import live_testing


logger = logging.getLogger(__name__)


if live_testing.enabled:
    def test_specific_messages():
        chat = wrapper.SEChatWrapper('stackexchange.com')
        # it shouldn't be necessary to log in for this test

        message1 = chat.get_message(15359027)

        assert message1.id == 15359027
        assert message1.text_content == '@JeremyBanks hello'
        assert message1.content_source == ":15358991 **hello**"
        assert message1.owner_user_id == 1251
        assert message1.room_id == 14219

        message2 = message1.parent

        assert message2.id == 15358991
        assert message2 is chat.get_message(15358991)
        assert message2.text_content == "@bot forever in my tests"
        assert message2.owner_user_id == 1251

        message3 = message2.parent

        assert message3.id == 15356758
        assert message3.owner_user_id == 97938
        assert message3.content_source == ":15356755 here's some attention"

        message4 = message3.parent

        assert message4.id == 15356755
        assert message4.owner_user_id == 97938
        assert message4.text_content == "and again!"
        assert message4.parent is None
