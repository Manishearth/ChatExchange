import logging

from chatexchange import Client

import live_testing


logger = logging.getLogger(__name__)


if live_testing.enabled:
    def test_specific_messages():
        client = Client('stackexchange.com')

        message1 = client.get_message(15359027)

        assert message1.id == 15359027
        assert message1.text_content == '@JeremyBanks hello'
        assert message1.content_source == ":15358991 **hello**"
        assert message1.owner.id == 1251
        assert message1.room.id == 14219

        message2 = message1.parent

        assert message2.id == 15358991
        assert message2 is client.get_message(15358991)
        assert message2.text_content == "@bot forever in my tests"
        assert message2.owner.id == 1251

        message3 = message2.parent
        message3.scrape_history = 'NOT EXPECTED TO BE CALLED'
        message3.scrape_transcript()

        assert message3.id == 15356758
        assert not message3.edited
        assert message3.editor is None
        assert not message3.pinned
        assert message3.pinners == []
        assert message3.pins == 0
        assert message3.owner.id == 97938

        message4 = message3.parent

        assert message4.id == 15356755
        assert message4.edited
        # assert message4.pinned
        assert message4.owner.id == 97938
        assert message4.text_content == "and again!"
        assert message4.parent is None

        message5 = client.get_message(15359293)
        message5.scrape_transcript = 'NOT EXPECTED TO BE CALLED'
        message5.scrape_history()

        assert message5.edited
        assert message5.edits == 1
        # assert message5.pinned
        # assert message5.pins == 1
        # assert set(p.id for p in message5.pinners) == {1251}
        assert message5.editor.id == 97938

        message6 = client.get_message(15493758)
        message6.scrape_transcript = 'NOT EXPECTED TO BE CALLED'
        message6.scrape_history()

        assert not message6.edited
        assert message6.edits == 0
        assert message6.editor is None
        # assert message6.pinned
        # assert message6.pins == 2
        # assert set(p.id for p in message6.pinners) == {1251, 97938}
