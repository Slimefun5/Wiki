"""Content model for the Slimefun wiki site: parsing, merging and URL rules.

No network and no HTML live here, so every rule below is testable against fixtures.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

COLOR_CODE = re.compile(r"[&§][0-9a-fk-orA-FK-OR]")


def strip_color(text: str) -> str:
    return COLOR_CODE.sub("", text).strip().strip("'\"")


def page_slug(display_name: str) -> str:
    """The prose filename for a display name, matching the existing pages/<slug>.md files."""
    return display_name.replace(" ", "-")


def item_url(plugin: str, item_id: str, base: str) -> str:
    return "{}/{}/{}/".format(base, plugin, item_id.lower())


def topic_url(topic_id: str, base: str) -> str:
    return "{}/topic/{}/".format(base, topic_id)


def addon_url(plugin: str, base: str) -> str:
    return "{}/addon/{}/".format(base, plugin)


def prose_url(slug: str, base: str) -> str:
    return "{}/{}/".format(base, slug)


@dataclass
class Item:
    id: str
    plugin: str
    addon_name: str
    name: str
    type_lines: List[str] = field(default_factory=list)
    description: List[str] = field(default_factory=list)
    stats: List[str] = field(default_factory=list)
    usage: List[str] = field(default_factory=list)
    wiki_lines: List[str] = field(default_factory=list)
    prose_html: Optional[str] = None
    prose_link: Optional[str] = None
    url: str = ""


@dataclass
class Topic:
    id: str
    title: str
    icon: str
    summary: str
    page: Optional[str] = None
    body: List[str] = field(default_factory=list)
    prose_html: Optional[str] = None
    item_ids: List[str] = field(default_factory=list)
    url: str = ""


@dataclass
class Prose:
    slug: str
    title: str
    html: str
    absorbed_by: Optional[str] = None
    url: str = ""


@dataclass
class Addon:
    plugin: str
    name: str
    items: List[Item] = field(default_factory=list)
    url: str = ""


@dataclass
class Site:
    items: List[Item] = field(default_factory=list)
    topics: List[Topic] = field(default_factory=list)
    prose: List[Prose] = field(default_factory=list)
    addons: List[Addon] = field(default_factory=list)
    collisions: List[str] = field(default_factory=list)

    def items_by_id(self) -> Dict[str, Item]:
        return {item.id: item for item in self.items}


import yaml


def _lines(block: dict, key: str) -> List[str]:
    value = block.get(key) or []
    return [strip_color(str(line)) for line in value]


def _load(text: str) -> dict:
    parsed = yaml.safe_load(text)
    return parsed if isinstance(parsed, dict) else {}


def parse_items_yaml(text: str, plugin: str, addon_name: str) -> List[Item]:
    """Parse one repo's languages/en/items.yml. Entries without a name carry nothing to show."""
    items = []

    for item_id, block in _load(text).items():
        if not isinstance(block, dict) or not block.get("name"):
            continue

        items.append(Item(
            id=str(item_id),
            plugin=plugin,
            addon_name=addon_name,
            name=strip_color(str(block["name"])),
            type_lines=_lines(block, "type"),
            description=_lines(block, "description"),
            stats=_lines(block, "stats"),
            usage=_lines(block, "usage"),
        ))

    return items


def parse_lines_yaml(text: str) -> Dict[str, List[str]]:
    """Parse an id-to-list resource: wiki/items.yml, wiki/mechanics.yml, wiki/topic-items.yml."""
    parsed = {}

    for key, value in _load(text).items():
        if isinstance(value, list):
            parsed[str(key)] = [strip_color(str(line)) for line in value]

    return parsed


def parse_topics_yaml(text: str) -> List[Topic]:
    topics = []

    for topic_id, block in _load(text).items():
        if not isinstance(block, dict):
            continue

        topics.append(Topic(
            id=str(topic_id),
            title=str(block.get("title", topic_id)),
            icon=str(block.get("icon", "PAPER")),
            summary=strip_color(str(block.get("summary", ""))),
            page=block.get("page"),
        ))

    return topics
