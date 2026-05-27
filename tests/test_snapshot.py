from stealth_browser.snapshot import SNAPSHOT_JS, PageSnapshot, RefElement


def make_snapshot(refs=None, markdown="Hello world"):
    return PageSnapshot(
        url="https://example.com",
        title="Example",
        refs=refs or [],
        markdown=markdown,
    )


def make_ref(index=0, role="button", label="Click me", tag="button", bbox=(10, 20, 100, 30)):
    return RefElement(index=index, role=role, label=label, tag=tag, bbox=bbox)


def test_to_dict_basic():
    snap = make_snapshot([make_ref()])
    d = snap.to_dict()
    assert d["url"] == "https://example.com"
    assert d["title"] == "Example"
    assert len(d["refs"]) == 1
    assert d["refs"][0]["label"] == "Click me"


def test_to_dict_screenshot_none():
    snap = make_snapshot()
    d = snap.to_dict()
    assert d["screenshot_b64"] is None


def test_to_llm_text_contains_url_and_title():
    snap = make_snapshot([make_ref()])
    text = snap.to_llm_text()
    assert "https://example.com" in text
    assert "Example" in text


def test_to_llm_text_lists_refs():
    refs = [make_ref(0, "button", "Submit"), make_ref(1, "link", "Home")]
    snap = make_snapshot(refs)
    text = snap.to_llm_text()
    assert "[0]" in text
    assert "Submit" in text
    assert "[1]" in text
    assert "Home" in text


def test_to_llm_text_max_chars():
    long_markdown = "x" * 5000
    snap = make_snapshot(markdown=long_markdown)
    text = snap.to_llm_text(max_chars=100)
    assert "x" * 101 not in text
    assert "x" * 100 in text


def test_to_llm_text_default_max_chars_3000():
    long_markdown = "y" * 4000
    snap = make_snapshot(markdown=long_markdown)
    text = snap.to_llm_text()
    assert "y" * 3001 not in text


def test_to_llm_text_empty_markdown():
    snap = PageSnapshot(url="https://x.com", title="X", refs=[], markdown="")
    text = snap.to_llm_text()
    assert "Content:" not in text


def test_snapshot_js_dedup_uses_position():
    assert "Math.round(r.x)" in SNAPSHOT_JS or "r.x" in SNAPSHOT_JS
    assert "Math.round(r.y)" in SNAPSHOT_JS or "r.y" in SNAPSHOT_JS


def test_ref_element_bbox_tuple():
    r = make_ref(bbox=(1.0, 2.0, 3.0, 4.0))
    assert r.bbox == (1.0, 2.0, 3.0, 4.0)


def test_to_dict_bbox_is_list():
    snap = make_snapshot([make_ref(bbox=(1, 2, 3, 4))])
    d = snap.to_dict()
    assert isinstance(d["refs"][0]["bbox"], list)
