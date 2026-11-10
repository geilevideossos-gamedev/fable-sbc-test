from voxhub_assistant.sentences import SentenceSplitter, clean_for_speech


def feed_all(deltas, **kwargs):
    splitter = SentenceSplitter(**kwargs)
    out = []
    for delta in deltas:
        out.extend(splitter.feed(delta))
    return out, splitter.flush()


def test_splits_as_text_streams_in():
    text = "The kitchen light is on. It is 21.5 degrees in the living room! Anything else?"
    deltas = [text[i : i + 5] for i in range(0, len(text), 5)]
    sentences, rest = feed_all(deltas)
    assert sentences == ["The kitchen light is on.", "It is 21.5 degrees in the living room!"]
    assert rest == ["Anything else?"]


def test_sentence_is_emitted_before_the_reply_is_complete():
    splitter = SentenceSplitter()
    assert splitter.feed("The lights are now off. And the") == ["The lights are now off."]
    assert splitter.feed(" heating is") == []
    assert splitter.flush() == ["And the heating is"]


def test_decimals_and_times_are_not_split():
    sentences, rest = feed_all(["It is 3.30pm and 21.5 degrees outside right now."])
    assert sentences == [] and rest == ["It is 3.30pm and 21.5 degrees outside right now."]


def test_short_fragments_are_merged():
    sentences, rest = feed_all(["Sure. Ok. The living room lamp is on now. Bye."])
    assert sentences == ["Sure. Ok. The living room lamp is on now."]
    assert rest == ["Bye."]


def test_newline_is_a_boundary():
    sentences, rest = feed_all(["Let me check that for you", "\n", "It is sunny today"])
    assert sentences == ["Let me check that for you"]
    assert rest == ["It is sunny today"]


def test_markdown_is_removed():
    assert clean_for_speech("**Done!** The `light` is _on_.") == "Done! The light is on ."
    assert clean_for_speech("- first\n- second") == "first second"
    assert clean_for_speech("See [the docs](https://example.com) now") == "See the docs now"
    assert clean_for_speech("# Title") == "Title"


def test_flush_on_empty_buffer():
    splitter = SentenceSplitter()
    assert splitter.flush() == []
    assert splitter.feed("   ") == []
    assert splitter.flush() == []
