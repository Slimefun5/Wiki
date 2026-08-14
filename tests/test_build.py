import json
import os

import pytest

from types import SimpleNamespace

from wiki.build import check_links, load_prose, write_site
from wiki.model import build_site


def _sources():
    return SimpleNamespace(
        repos=[SimpleNamespace(plugin="slimefun", name="Slimefun")],
        items_yaml={"slimefun": "GOLD_PAN:\n  name: '&6Gold Pan'\n"},
        core_wiki_items="GOLD_PAN:\n  - '&7Sifts gravel.'\n",
        core_mechanics="cargo:\n  - '&7Cargo moves items.'\n",
        core_topics="cargo:\n  title: Cargo\n  icon: HOPPER\n  summary: '&7Move items'\n",
        core_topic_items="cargo:\n  - 'GOLD_PAN'\n",
    )


def test_load_prose_renders_markdown_and_rewrites_github_wiki_links(tmp_path):
    pages = tmp_path / "pages"
    pages.mkdir()
    (pages / "Common-Issues.md").write_text(
        "# FAQ\n\nSee [cargo](https://github.com/Slimefun5/Slimefun5/wiki/Cargo-Management).\n",
        encoding="utf-8")

    prose = load_prose(str(pages), "/wiki")

    assert "Common-Issues" in prose
    assert "/wiki/Cargo-Management/" in prose["Common-Issues"]
    assert "github.com" not in prose["Common-Issues"]


def test_write_site_emits_every_page_and_the_search_index(tmp_path):
    site = build_site(_sources(), prose={"Gold-Pan": "<p>Guide.</p>"}, base="/wiki")
    out = str(tmp_path / "out")

    write_site(site, out, "/wiki")

    assert os.path.exists(os.path.join(out, "index.html"))
    assert os.path.exists(os.path.join(out, "slimefun", "gold_pan", "index.html"))
    assert os.path.exists(os.path.join(out, "topic", "cargo", "index.html"))
    assert os.path.exists(os.path.join(out, "addon", "slimefun", "index.html"))
    assert os.path.exists(os.path.join(out, "guides", "index.html"))
    assert os.path.exists(os.path.join(out, ".nojekyll"))
    assert os.path.exists(os.path.join(out, "assets", "wiki.css"))

    index = json.load(open(os.path.join(out, "assets", "search-index.json"), encoding="utf-8"))
    assert any(e["u"] == "/wiki/slimefun/gold_pan/" for e in index)


def test_absorbed_prose_still_serves_a_redirect(tmp_path):
    site = build_site(_sources(), prose={"Gold-Pan": "<p>Guide.</p>"}, base="/wiki")
    out = str(tmp_path / "out")

    write_site(site, out, "/wiki")

    redirect = open(os.path.join(out, "Gold-Pan", "index.html"), encoding="utf-8").read()
    assert "/wiki/slimefun/gold_pan/" in redirect


def test_write_site_raises_when_an_item_produced_no_file(tmp_path):
    site = build_site(_sources(), prose={}, base="/wiki")
    site.items[0].url = ""

    with pytest.raises(AssertionError):
        write_site(site, str(tmp_path / "out"), "/wiki")


def test_check_links_finds_a_dangling_internal_href(tmp_path):
    out = tmp_path / "out"
    (out / "a").mkdir(parents=True)
    (out / "a" / "index.html").write_text('<a href="/wiki/nope/">x</a>', encoding="utf-8")

    assert check_links(str(out), "/wiki") == ["/wiki/nope/"]


def test_check_links_accepts_a_written_page(tmp_path):
    out = tmp_path / "out"
    (out / "a").mkdir(parents=True)
    (out / "a" / "index.html").write_text('<a href="/wiki/a/">x</a>', encoding="utf-8")

    assert check_links(str(out), "/wiki") == []


def test_check_links_unescapes_html_entities_before_checking(tmp_path):
    out = tmp_path / "out"
    (out / "it's_a_test").mkdir(parents=True)
    (out / "it's_a_test" / "index.html").write_text("ok", encoding="utf-8")
    (out / "a").mkdir(parents=True)
    (out / "a" / "index.html").write_text(
        '<a href="/wiki/it&#x27;s_a_test/">x</a>', encoding="utf-8")

    assert check_links(str(out), "/wiki") == []


def _family_sources():
    return SimpleNamespace(
        repos=[SimpleNamespace(plugin="souljars", name="SoulJars")],
        items_yaml={"souljars": (
            "'%MOB%_SOUL_JAR':\n"
            "  name: '&6%mob% Soul Jar'\n"
            "  type:\n  - '&7&oGadget'\n"
            "  description:\n  - '&fTraps a %mob%.'\n"
        )},
        core_wiki_items=None,
        core_mechanics=None,
        core_topics=None,
        core_topic_items=None,
    )


def test_write_site_emits_a_family_page_families_json_and_a_404_page(tmp_path):
    site = build_site(_family_sources(), prose={}, base="/wiki")
    out = str(tmp_path / "out")

    write_site(site, out, "/wiki")

    assert os.path.exists(os.path.join(out, "souljars", "soul_jar-family", "index.html"))
    assert os.path.exists(os.path.join(out, "404.html"))
    assert os.path.exists(os.path.join(out, "assets", "families.json"))

    families = json.load(open(os.path.join(out, "assets", "families.json"), encoding="utf-8"))
    assert families[0]["plugin"] == "souljars"
    assert families[0]["regex"] == "^(.+)_soul_jar$"
    assert "%mob%" in families[0]["name"]

    family_page = open(os.path.join(out, "souljars", "soul_jar-family", "index.html"),
                       encoding="utf-8").read()
    assert "any mob" in family_page
    assert "%mob%" not in family_page

    addon_page = open(os.path.join(out, "addon", "souljars", "index.html"),
                      encoding="utf-8").read()
    assert "/wiki/souljars/soul_jar-family/" in addon_page
