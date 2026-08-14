import json

from wiki.model import Addon, Item, Prose, Site, Topic
from wiki.render import (render_addon_index, render_item_page, render_landing, render_redirect,
                         render_topic_page, search_index)


def _item(**overrides):
    base = dict(id="GOLD_PAN", plugin="slimefun", addon_name="Slimefun", name="Gold Pan",
                type_lines=["Gadget"], description=["Sifts gravel."], stats=["+ Luck"],
                usage=["Right-click gravel."], wiki_lines=["A great early resource source."],
                url="/wiki/slimefun/gold_pan/")
    base.update(overrides)
    return Item(**base)


def test_item_page_renders_every_block_in_order():
    html = render_item_page(_item(prose_html="<p>Long form.</p>"), "/wiki")

    positions = [html.index(marker) for marker in
                 ["Gadget", "Sifts gravel.", "+ Luck", "Right-click gravel.",
                  "A great early resource source.", "Long form."]]
    assert positions == sorted(positions)
    assert "Slimefun" in html


def test_item_page_links_to_a_topic_that_claimed_its_prose():
    html = render_item_page(_item(prose_link="/wiki/topic/smeltery/"), "/wiki")
    assert 'href="/wiki/topic/smeltery/"' in html


def test_item_page_escapes_html_in_names():
    html = render_item_page(_item(name="Gold <Pan>"), "/wiki")
    assert "Gold &lt;Pan&gt;" in html
    assert "<Pan>" not in html


def test_topic_page_lists_its_items_as_links():
    topic = Topic(id="cargo", title="Cargo Networks", icon="HOPPER", summary="Move items",
                  body=["Cargo moves items.", "", "Build a network."], item_ids=["GOLD_PAN"],
                  url="/wiki/topic/cargo/")
    html = render_topic_page(topic, {"GOLD_PAN": _item()}, "/wiki")

    assert 'href="/wiki/slimefun/gold_pan/"' in html
    assert "Cargo moves items." in html
    assert "Build a network." in html


def test_topic_page_skips_unknown_item_ids():
    topic = Topic(id="cargo", title="Cargo", icon="HOPPER", summary="", item_ids=["NOPE"],
                  url="/wiki/topic/cargo/")
    html = render_topic_page(topic, {}, "/wiki")
    assert "NOPE" not in html


def test_addon_index_shows_the_item_count():
    addon = Addon(plugin="networks", name="Networks",
                  items=[_item(id="A", name="A"), _item(id="B", name="B")],
                  url="/wiki/addon/networks/")
    html = render_addon_index(addon, "/wiki")

    assert "2 items" in html
    assert "Networks" in html


def test_redirect_targets_the_canonical_url():
    html = render_redirect("/wiki/slimefun/gold_pan/")
    assert 'url=/wiki/slimefun/gold_pan/' in html
    assert 'rel="canonical"' in html


def test_search_index_covers_items_topics_and_guides():
    site = Site(items=[_item()],
                topics=[Topic(id="cargo", title="Cargo", icon="HOPPER", summary="",
                              url="/wiki/topic/cargo/")],
                prose=[Prose(slug="Common-Issues", title="Common Issues", html="",
                             url="/wiki/Common-Issues/")])
    index = search_index(site)

    assert {entry["k"] for entry in index} == {"item", "topic", "guide"}
    assert {"n": "Gold Pan", "u": "/wiki/slimefun/gold_pan/", "k": "item", "a": "Slimefun"} in index
    json.dumps(index)


def test_search_index_omits_absorbed_prose():
    site = Site(prose=[Prose(slug="Gold-Pan", title="Gold Pan", html="",
                             url="/wiki/Gold-Pan/", absorbed_by="/wiki/slimefun/gold_pan/")])
    assert search_index(site) == []


def test_landing_reports_the_real_counts():
    site = Site(items=[_item()],
                addons=[Addon(plugin="slimefun", name="Slimefun", items=[_item()],
                              url="/wiki/addon/slimefun/")],
                prose=[Prose(slug="Common-Issues", title="Common Issues", html="",
                             url="/wiki/Common-Issues/")])
    html = render_landing(site, "/wiki")

    assert "1 item" in html
    assert 'href="/wiki/addon/slimefun/"' in html
