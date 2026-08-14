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


def build_site(sources, prose: Dict[str, str], base: str) -> Site:
    """Merge every source into one page per subject.

    Topics claim their prose before items do, so a page named by a topic's 'page' key never also
    appears inlined on an item page.
    """
    site = Site()

    for repo in sources.repos:
        text = sources.items_yaml.get(repo.plugin)

        if not text:
            continue

        items = parse_items_yaml(text, repo.plugin, repo.name)

        for item in items:
            item.url = item_url(item.plugin, item.id, base)

        site.items.extend(items)
        site.addons.append(Addon(plugin=repo.plugin, name=repo.name, items=items,
                                 url=addon_url(repo.plugin, base)))

    authored = parse_lines_yaml(sources.core_wiki_items or "")
    for item in site.items:
        item.wiki_lines = authored.get(item.id, [])

    mechanics = parse_lines_yaml(sources.core_mechanics or "")
    topic_items = parse_lines_yaml(sources.core_topic_items or "")
    claimed = {}  # slug -> (url, claimant description) for the message below

    for topic in parse_topics_yaml(sources.core_topics or ""):
        topic.url = topic_url(topic.id, base)
        topic.body = mechanics.get(topic.id, [])
        topic.item_ids = topic_items.get(topic.id, [])

        if topic.page:
            if topic.page in prose:
                topic.prose_html = prose[topic.page]
                claimed[topic.page] = (topic.url, "topic '{}'".format(topic.id))
            else:
                site.collisions.append(
                    "topic '{}' names prose page '{}' which does not exist".format(topic.id, topic.page))

        site.topics.append(topic)

    by_slug = {}
    for item in site.items:
        by_slug.setdefault(page_slug(item.name), []).append(item)

    for slug, html in sorted(prose.items()):
        target, claimant = claimed.get(slug, (None, None))

        for item in by_slug.get(slug, []):
            if target:
                item.prose_link = target
                site.collisions.append(
                    "{} is claimed by {}; item {} links to it instead".format(slug, claimant, item.id))
            else:
                item.prose_html = html
                target = item.url
                claimant = "item {}".format(item.id)

        site.prose.append(Prose(slug=slug, title=slug.replace("-", " "), html=html,
                                absorbed_by=target, url=prose_url(slug, base)))

    return site
