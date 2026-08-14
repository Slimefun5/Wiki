from wiki.model import Item, page_slug, strip_color, item_url


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
