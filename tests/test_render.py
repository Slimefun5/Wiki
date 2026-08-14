import json

from wiki.model import Addon, Item, ItemFamily, Prose, Site, Topic
from wiki.render import (_block, _paragraphs, render_addon_index, render_item_page, render_landing,
                         render_redirect, render_topic_page, search_index, render_family_page,
                         render_404_page, families_json)


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


def test_item_page_escapes_a_quote_in_the_plugin_segment():
    html = render_item_page(_item(plugin='slimefun" onmouseover="alert(1)'), "/wiki")
    assert '" onmouseover="alert(1)' not in html
    assert "&quot; onmouseover=&quot;alert(1)" in html


def test_item_page_escapes_a_quote_in_the_prose_link():
    html = render_item_page(_item(prose_link='/wiki/x/"><script>alert(1)</script>'), "/wiki")
    assert "<script>alert(1)</script>" not in html


def test_topic_page_lists_its_items_as_links():
    topic = Topic(id="cargo", title="Cargo Networks", icon="HOPPER", summary="Move items",
                  body=["Cargo moves items.", "", "Build a network."], item_ids=["GOLD_PAN"],
                  url="/wiki/topic/cargo/")
    html = render_topic_page(topic, {"GOLD_PAN": _item()}, "/wiki")

    assert 'href="/wiki/slimefun/gold_pan/"' in html
    assert "Cargo moves items." in html
    assert "Build a network." in html


def test_topic_page_escapes_a_quote_in_an_item_url():
    quoted_item = _item(url='/wiki/x/"><script>alert(1)</script>')
    topic = Topic(id="cargo", title="Cargo", icon="HOPPER", summary="", item_ids=["GOLD_PAN"],
                  url="/wiki/topic/cargo/")
    html = render_topic_page(topic, {"GOLD_PAN": quoted_item}, "/wiki")
    assert "<script>alert(1)</script>" not in html


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


def _family(**overrides):
    base = dict(plugin="souljars", addon_name="SoulJars", template_id="%MOB%_SOUL_JAR",
                name="%mob% Soul Jar", type_lines=["Gadget"], description=["Traps a %mob%."],
                stats=["+ Soul"], usage=["Right-click a %mob%."],
                regex="^(.+)_soul_jar$", url="/wiki/souljars/soul_jar-family/")
    base.update(overrides)
    return ItemFamily(**base)


def test_family_page_substitutes_any_mob_for_the_placeholder():
    html = render_family_page(_family(), "/wiki")

    assert "any mob Soul Jar" in html
    assert "Traps a any mob." in html
    assert "%mob%" not in html


def test_family_page_shows_the_addon_and_back_link():
    html = render_family_page(_family(), "/wiki")
    assert 'href="/wiki/addon/souljars/"' in html
    assert "SoulJars" in html


def test_families_json_keeps_the_mob_placeholder_intact():
    site = Site(families=[_family()])
    entries = json.loads(families_json(site))

    assert entries == [{
        "plugin": "souljars", "regex": "^(.+)_soul_jar$", "url": "/wiki/souljars/soul_jar-family/",
        "addon": "SoulJars", "name": "%mob% Soul Jar", "type": ["Gadget"],
        "description": ["Traps a %mob%."], "stats": ["+ Soul"], "usage": ["Right-click a %mob%."],
    }]


def test_search_index_includes_families_with_a_distinct_kind():
    site = Site(families=[_family()])
    index = search_index(site)

    assert index == [{"n": "any mob Soul Jar", "u": "/wiki/souljars/soul_jar-family/",
                      "k": "family", "a": "SoulJars"}]


def test_addon_index_links_to_its_families():
    addon = Addon(plugin="souljars", name="SoulJars", url="/wiki/addon/souljars/")
    html = render_addon_index(addon, "/wiki", families=[_family()])
    assert 'href="/wiki/souljars/soul_jar-family/"' in html


def test_addon_index_without_families_is_unaffected():
    addon = Addon(plugin="souljars", name="SoulJars", url="/wiki/addon/souljars/")
    html = render_addon_index(addon, "/wiki")
    assert "Item families" not in html


def test_404_page_falls_back_to_a_not_found_message_with_an_index_link():
    html = render_404_page("/wiki")
    assert "Page not found" in html
    assert 'href="/wiki/"' in html
    assert "assets/families.json" in html


def test_404_page_has_no_em_dash_or_en_dash():
    html = render_404_page("/wiki")
    assert "—" not in html
    assert "–" not in html


def test_redirect_targets_the_canonical_url():
    html = render_redirect("/wiki/slimefun/gold_pan/")
    assert 'url=/wiki/slimefun/gold_pan/' in html
    assert 'rel="canonical"' in html


def test_redirect_escapes_a_quote_in_the_target():
    html = render_redirect('/wiki/x/"><script>alert(1)</script>')
    assert "<script>alert(1)</script>" not in html
    assert html.count("&quot;") >= 3


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


def test_block_handles_an_empty_list_and_an_all_blank_list():
    assert _block([]) == ""
    assert _block(["", ""]) == ""


def test_block_ignores_leading_and_trailing_blank_lines():
    result = _block(["", "First", "Second", ""])
    assert result.count("<li>") == 2
    assert "First" in result and "Second" in result


def test_paragraphs_handles_an_empty_list_and_an_all_blank_list():
    assert _paragraphs([]) == ""
    assert _paragraphs(["", "", ""]) == ""


def test_paragraphs_ignores_leading_and_trailing_blank_lines():
    assert _paragraphs(["", "First line", ""]) == "<p>First line</p>\n"


def test_paragraphs_treats_consecutive_blank_lines_as_a_single_break():
    result = _paragraphs(["A", "", "", "", "B"])
    assert result == "<p>A</p>\n<p>B</p>\n"
    assert "<p></p>" not in result
