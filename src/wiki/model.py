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
