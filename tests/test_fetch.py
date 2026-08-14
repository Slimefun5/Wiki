import json

import pytest

from wiki.fetch import MissingRequiredSource, fetch_sources, parse_manifest, raw_url

MANIFEST = json.dumps({
    "core": {"repo": "Slimefun5/Slimefun5", "name": "Slimefun",
             "pluginName": "Slimefun", "defaultBranch": "stable"},
    "libraries": [{"repo": "Slimefun5/InfinityLib", "name": "Infinity Lib",
                   "pluginName": None, "defaultBranch": "stable"}],
    "addons": [{"repo": "Slimefun5/Networks", "name": "Networks",
                "pluginName": "Networks", "defaultBranch": "stable"},
               {"repo": "Slimefun5/InfinityExpansion", "name": "Infinity Expansion",
                "pluginName": "InfinityExpansion", "defaultBranch": "main"}],
})


def test_raw_url_points_at_the_pinned_ref():
    assert raw_url("Slimefun5/Networks", "stable", "src/x.yml") == \
        "https://raw.githubusercontent.com/Slimefun5/Networks/stable/src/x.yml"


def test_parse_manifest_puts_core_first_and_drops_libraries():
    repos = parse_manifest(MANIFEST)

    assert [r.plugin for r in repos] == ["slimefun", "networks", "infinityexpansion"]
    assert repos[0].repo == "Slimefun5/Slimefun5"
    assert repos[2].ref == "main"
    assert repos[2].name == "Infinity Expansion"


def test_fetch_sources_skips_a_failing_addon_but_keeps_building():
    def fetcher(url):
        if "Networks" in url:
            return None
        if "languages/en/items.yml" in url:
            return "X:\n  name: '&7X'\n"
        return "cargo:\n  - '&7body'\n"

    sources = fetch_sources(MANIFEST, fetcher=fetcher)

    assert "slimefun" in sources.items_yaml
    assert "networks" not in sources.items_yaml
    assert any("Networks" in s for s in sources.skipped)


def test_fetch_sources_fails_hard_without_core_items():
    def fetcher(url):
        return None if "Slimefun5/Slimefun5" in url else "X:\n  name: '&7X'\n"

    with pytest.raises(MissingRequiredSource):
        fetch_sources(MANIFEST, fetcher=fetcher)


def test_missing_core_wiki_resources_only_warn():
    def fetcher(url):
        return None if "/wiki/" in url else "X:\n  name: '&7X'\n"

    sources = fetch_sources(MANIFEST, fetcher=fetcher)

    assert sources.core_topics is None
    assert sources.core_mechanics is None
    assert sources.items_yaml["slimefun"] is not None


def test_core_ref_override_wins_over_the_manifest():
    seen = []

    def fetcher(url):
        seen.append(url)
        return "X:\n  name: '&7X'\n"

    fetch_sources(MANIFEST, core_ref="experimental", fetcher=fetcher)

    core_urls = [u for u in seen if "Slimefun5/Slimefun5" in u]
    assert core_urls
    assert all("/experimental/" in u for u in core_urls)
