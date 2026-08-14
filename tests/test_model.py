from wiki.model import Item, page_slug, strip_color, item_url, parse_items_yaml, parse_lines_yaml, parse_topics_yaml

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


def test_item_url_matches_wikilinks():
    assert item_url("slimefun", "ANCIENT_ALTAR", "/wiki") == "/wiki/slimefun/ancient_altar/"
    assert item_url("infinityexpansion", "ADVANCED_CHARGER", "/wiki") == \
        "/wiki/infinityexpansion/advanced_charger/"


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
