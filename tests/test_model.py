import re

from wiki.model import (Item, page_slug, plugin_slug, strip_color, item_url, parse_items_yaml,
                        parse_lines_yaml, parse_topics_yaml, is_family_template, family_slug,
                        family_url, family_regex_source)

ITEMS_YAML = """
ADVANCED_INDUSTRIAL_MINER:
  name: '&cAdvanced Industrial Miner'
  type:
  - '&7&oMultiblock'
  description:
  - '&fThis Multiblock will mine any Ores'
  stats:
  - '&a+ Silk Touch'
ALUMINUM_DUST:
  name: '&6Aluminum Dust'
  type:
  - '&7&oResource'
"""


def test_strip_color_removes_codes_and_quotes():
    assert strip_color("'&bAluminum Ingot'") == "Aluminum Ingot"
    assert strip_color("&cAdvanced &fGeoMiner") == "Advanced GeoMiner"


def test_page_slug_matches_the_existing_prose_filenames():
    assert page_slug("Cargo Management") == "Cargo-Management"
    assert page_slug("Ancient Altar") == "Ancient-Altar"


def test_plugin_slug_lowercases_a_plain_name():
    assert plugin_slug("Slimefun") == "slimefun"
    assert plugin_slug("InfinityExpansion") == "infinityexpansion"


def test_plugin_slug_replaces_a_space_a_dot_and_a_plus():
    assert plugin_slug("My Addon") == "my-addon"
    assert plugin_slug("Addon.Name") == "addon-name"
    assert plugin_slug("C++Tools") == "c--tools"


# pluginName values from infra/manifest/addons.json (core + all 21 addons); hardcoded rather than
# read from the sibling infra/manifest checkout, which is a separate repo not present in this
# repo's CI checkout and whose absolute path is host-specific.
REAL_PLUGIN_NAMES = [
    "Slimefun", "Galactifun", "SlimefunLuckyBlocks", "ExoticGarden", "ExtraGear",
    "LiteXpansion", "SensibleToolbox", "InfinityExpansion", "SlimeTinker",
    "FluffyMachines", "DynaTech", "ChestTerminal", "SFAdvancements", "MissileWarfare",
    "Networks", "SoulJars", "FastMachines", "GeneticChickengineering", "Supreme",
    "FoxyMachines", "SimpleMaterialGenerators", "SimpleUtils",
]


def _core_wikilinks_slug(name: str) -> str:
    """Independent re-implementation of core's Java WikiLinks.slug(), so this test can catch
    plugin_slug drifting from the rule it is meant to mirror."""
    return re.sub(r"[^a-z0-9_-]", "-", name.lower())


def test_plugin_slug_matches_core_rule_for_every_real_plugin_name():
    for name in REAL_PLUGIN_NAMES:
        assert plugin_slug(name) == _core_wikilinks_slug(name)


def test_item_url_matches_wikilinks():
    assert item_url("slimefun", "ANCIENT_ALTAR", "/wiki") == "/wiki/slimefun/ancient_altar/"
    assert item_url("infinityexpansion", "ADVANCED_CHARGER", "/wiki") == \
        "/wiki/infinityexpansion/advanced_charger/"


def test_item_url_is_unchanged_for_ids_already_in_the_allowed_charset():
    assert item_url("slimefun", "ANCIENT_ALTAR", "/wiki") == "/wiki/slimefun/ancient_altar/"
    assert item_url("infinityexpansion", "ADVANCED_CHARGER", "/wiki") == \
        "/wiki/infinityexpansion/advanced_charger/"


def test_item_url_sanitizes_reserved_characters_in_the_id():
    assert item_url("slimetinker", "WHO_NEEDS_PRESSURE_PLATES?_TRAIT", "/wiki") == \
        "/wiki/slimetinker/who_needs_pressure_plates-_trait/"
    assert item_url("slimetinker", "MOB?S,GREAT!ITEM+NAME'S", "/wiki") == \
        "/wiki/slimetinker/mob-s-great-item-name-s/"


def test_is_family_template_detects_the_percent_token():
    assert is_family_template("%MOB%_SOUL_JAR")
    assert not is_family_template("GOLD_PAN")


def test_is_family_template_rejects_a_stray_percent_with_no_full_token():
    assert not is_family_template("SOME_50%_ITEM")


def test_family_slug_strips_the_token_and_dangling_underscores():
    assert family_slug("%MOB%_SOUL_JAR") == "soul_jar-family"
    assert family_slug("FILLED_%MOB%_SOUL_JAR") == "filled_soul_jar-family"
    assert family_slug("%MOB%_BROKEN_SPAWNER") == "broken_spawner-family"
    assert family_slug("GHOST_BLOCK_%MOB%") == "ghost_block-family"


def test_family_url_uses_the_family_slug():
    assert family_url("souljars", "%MOB%_SOUL_JAR", "/wiki") == "/wiki/souljars/soul_jar-family/"


def test_family_regex_source_anchors_and_captures_the_token():
    assert family_regex_source("%MOB%_SOUL_JAR") == "^(.+)_soul_jar$"
    assert family_regex_source("FILLED_%MOB%_SOUL_JAR") == "^filled_(.+)_soul_jar$"
    assert family_regex_source("%MOB%_BROKEN_SPAWNER") == "^(.+)_broken_spawner$"
    assert family_regex_source("GHOST_BLOCK_%MOB%") == "^ghost_block_(.+)$"


def test_item_defaults_are_empty_not_none():
    item = Item(id="X", plugin="slimefun", addon_name="Slimefun", name="X")
    assert item.type_lines == []
    assert item.description == []
    assert item.stats == []
    assert item.usage == []
    assert item.wiki_lines == []
    assert item.prose_html is None


def test_parse_items_yaml_reads_every_block():
    items = parse_items_yaml(ITEMS_YAML, "slimefun", "Slimefun")

    assert [i.id for i in items] == ["ADVANCED_INDUSTRIAL_MINER", "ALUMINUM_DUST"]

    miner = items[0]
    assert miner.name == "Advanced Industrial Miner"
    assert miner.plugin == "slimefun"
    assert miner.addon_name == "Slimefun"
    assert miner.type_lines == ["Multiblock"]
    assert miner.description == ["This Multiblock will mine any Ores"]
    assert miner.stats == ["+ Silk Touch"]
    assert miner.usage == []


def test_parse_items_yaml_skips_entries_without_a_name():
    items = parse_items_yaml("BROKEN:\n  type:\n  - '&7x'\n", "slimefun", "Slimefun")
    assert items == []


def test_parse_lines_yaml_returns_id_to_lines():
    parsed = parse_lines_yaml("GOLD_PAN:\n  - '&7Right-click gravel'\n  - '&eGreat early on.'\n")
    assert parsed == {"GOLD_PAN": ["Right-click gravel", "Great early on."]}


def test_parse_topics_yaml_reads_page_mapping_and_order():
    topics = parse_topics_yaml(
        "cargo:\n"
        "  title: Cargo Networks\n"
        "  icon: HOPPER\n"
        "  summary: '&7Move items automatically'\n"
        "  page: Cargo-Management\n"
        "research:\n"
        "  title: Research\n"
        "  icon: EXPERIENCE_BOTTLE\n"
        "  summary: '&7Unlock items'\n"
    )

    assert [t.id for t in topics] == ["cargo", "research"]
    assert topics[0].title == "Cargo Networks"
    assert topics[0].summary == "Move items automatically"
    assert topics[0].page == "Cargo-Management"
    assert topics[1].page is None


from types import SimpleNamespace

from wiki.model import build_site


def _sources(**overrides):
    base = dict(
        repos=[SimpleNamespace(plugin="slimefun", name="Slimefun"),
               SimpleNamespace(plugin="networks", name="Networks")],
        items_yaml={
            "slimefun": "SMELTERY:\n  name: '&7Smeltery'\n  type:\n  - '&7&oMultiblock'\n"
                        "GOLD_PAN:\n  name: '&6Gold Pan'\n",
            "networks": "NTW_GRID:\n  name: '&bNetwork Grid'\n",
        },
        core_wiki_items="GOLD_PAN:\n  - '&7Right-click gravel to sift.'\n",
        core_mechanics="cargo:\n  - '&7Cargo moves items.'\n",
        core_topics="cargo:\n  title: Cargo Networks\n  icon: HOPPER\n"
                    "  summary: '&7Move items'\n  page: Cargo-Management\n",
        core_topic_items="cargo:\n  - 'GOLD_PAN'\n",
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_items_carry_authored_wiki_lines_and_a_canonical_url():
    site = build_site(_sources(), prose={}, base="/wiki")
    gold_pan = site.items_by_id()["GOLD_PAN"]

    assert gold_pan.wiki_lines == ["Right-click gravel to sift."]
    assert gold_pan.url == "/wiki/slimefun/gold_pan/"


def test_addon_items_are_grouped_and_counted():
    site = build_site(_sources(), prose={}, base="/wiki")

    assert [(a.plugin, len(a.items)) for a in site.addons] == [("slimefun", 2), ("networks", 1)]
    assert site.items_by_id()["NTW_GRID"].url == "/wiki/networks/ntw_grid/"


def test_prose_is_absorbed_into_the_matching_item_and_redirects():
    site = build_site(_sources(), prose={"Gold-Pan": "<p>All about the Gold Pan.</p>"}, base="/wiki")

    assert site.items_by_id()["GOLD_PAN"].prose_html == "<p>All about the Gold Pan.</p>"
    absorbed = [p for p in site.prose if p.slug == "Gold-Pan"][0]
    assert absorbed.absorbed_by == "/wiki/slimefun/gold_pan/"


def test_unmatched_prose_stays_a_standalone_guide():
    site = build_site(_sources(), prose={"Common-Issues": "<p>FAQ.</p>"}, base="/wiki")
    guide = [p for p in site.prose if p.slug == "Common-Issues"][0]

    assert guide.absorbed_by is None
    assert guide.url == "/wiki/Common-Issues/"
    assert guide.title == "Common Issues"


def test_topic_wins_a_contested_prose_page_and_the_item_links_to_it():
    prose = {"Smeltery": "<p>Smeltery guide.</p>"}
    topics = "smeltery:\n  title: Smeltery\n  icon: FURNACE\n  summary: '&7Alloys'\n  page: Smeltery\n"
    site = build_site(_sources(core_topics=topics), prose=prose, base="/wiki")

    smeltery_item = site.items_by_id()["SMELTERY"]
    assert smeltery_item.prose_html is None
    assert smeltery_item.prose_link == "/wiki/topic/smeltery/"
    assert site.topics[0].prose_html == "<p>Smeltery guide.</p>"
    assert "Smeltery is claimed by topic 'smeltery'; item SMELTERY links to it instead" in site.collisions

    smeltery_prose = [p for p in site.prose if p.slug == "Smeltery"][0]
    assert smeltery_prose.absorbed_by == site.topics[0].url


def test_two_items_sharing_a_slug_the_first_wins_and_the_message_names_the_item():
    site = build_site(
        _sources(
            repos=[SimpleNamespace(plugin="slimefun", name="Slimefun"),
                   SimpleNamespace(plugin="networks", name="Networks")],
            items_yaml={
                "slimefun": "GOLD_DUST:\n  name: '&6Gold Dust'\n",
                "networks": "NTW_GOLD_DUST:\n  name: '&6Gold Dust'\n",
            },
        ),
        prose={"Gold-Dust": "<p>All about Gold Dust.</p>"},
        base="/wiki")

    core_item = site.items_by_id()["GOLD_DUST"]
    addon_item = site.items_by_id()["NTW_GOLD_DUST"]

    assert core_item.prose_html == "<p>All about Gold Dust.</p>"
    assert addon_item.prose_html is None
    assert addon_item.prose_link == core_item.url
    assert ("Gold-Dust is claimed by item GOLD_DUST; item NTW_GOLD_DUST links to it instead"
            in site.collisions)


def test_topic_page_naming_a_missing_prose_slug_is_reported():
    topics = "smeltery:\n  title: Smeltery\n  icon: FURNACE\n  summary: '&7Alloys'\n  page: Nonexistent-Page\n"
    site = build_site(_sources(core_topics=topics), prose={}, base="/wiki")

    assert site.topics[0].prose_html is None
    assert "topic 'smeltery' names prose page 'Nonexistent-Page' which does not exist" in site.collisions


def test_topics_carry_body_and_item_tiles():
    site = build_site(_sources(), prose={}, base="/wiki")
    cargo = site.topics[0]

    assert cargo.body == ["Cargo moves items."]
    assert cargo.item_ids == ["GOLD_PAN"]
    assert cargo.url == "/wiki/topic/cargo/"


def test_family_templates_are_excluded_from_normal_items_and_addon_counts():
    site = build_site(
        _sources(
            repos=[SimpleNamespace(plugin="souljars", name="SoulJars")],
            items_yaml={"souljars": "'%MOB%_SOUL_JAR':\n  name: '&6%mob% Soul Jar'\n"},
            core_wiki_items=None, core_mechanics=None, core_topics=None, core_topic_items=None),
        prose={}, base="/wiki")

    assert site.items == []
    assert site.addons[0].items == []
    assert len(site.families) == 1

    family = site.families[0]
    assert family.plugin == "souljars"
    assert family.addon_name == "SoulJars"
    assert family.name == "%mob% Soul Jar"
    assert family.url == "/wiki/souljars/soul_jar-family/"
    assert family.regex == "^(.+)_soul_jar$"


def test_a_stray_percent_with_no_full_token_is_an_ordinary_sanitized_item():
    site = build_site(
        _sources(
            repos=[SimpleNamespace(plugin="slimefun", name="Slimefun")],
            items_yaml={"slimefun": "SOME_50%_ITEM:\n  name: '&6Some Item'\n"},
            core_wiki_items=None, core_mechanics=None, core_topics=None, core_topic_items=None),
        prose={}, base="/wiki")

    assert site.families == []
    assert [i.id for i in site.items] == ["SOME_50%_ITEM"]
    assert site.items[0].url == "/wiki/slimefun/some_50-_item/"


def test_family_extraction_orders_more_specific_templates_first():
    site = build_site(
        _sources(
            repos=[SimpleNamespace(plugin="souljars", name="SoulJars")],
            items_yaml={"souljars":
                "'%MOB%_SOUL_JAR':\n  name: '&6%mob% Soul Jar'\n"
                "'FILLED_%MOB%_SOUL_JAR':\n  name: '&6Filled %mob% Soul Jar'\n"},
            core_wiki_items=None, core_mechanics=None, core_topics=None, core_topic_items=None),
        prose={}, base="/wiki")

    assert [f.template_id for f in site.families] == ["FILLED_%MOB%_SOUL_JAR", "%MOB%_SOUL_JAR"]


def test_missing_core_wiki_resources_degrade_to_an_empty_site_section():
    site = build_site(
        _sources(core_wiki_items=None, core_mechanics=None, core_topics=None, core_topic_items=None),
        prose={}, base="/wiki")

    assert site.topics == []
    assert site.items_by_id()["GOLD_PAN"].wiki_lines == []
