"""Content model for the Slimefun wiki site: parsing, merging and URL rules.

No network and no HTML live here, so every rule below is testable against fixtures.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, NamedTuple, Optional

import yaml

COLOR_CODE = re.compile(r"[&§][0-9a-fk-orA-FK-OR]")


def strip_color(text: str) -> str:
    return COLOR_CODE.sub("", text).strip()


def page_slug(display_name: str) -> str:
    """The prose filename for a display name, matching the existing pages/<slug>.md files."""
    return display_name.replace(" ", "-")


def plugin_slug(name: str) -> str:
    """Mirrors core's Java `WikiLinks.slug()` so the in-game "View in Wiki" link and this
    generator always build the same URL segment for a plugin name."""
    return re.sub(r"[^a-z0-9_-]", "-", name.lower())


def item_url(plugin: str, item_id: str, base: str) -> str:
    """Routes the id through the same rule as the plugin segment (`WikiLinks.slug()`), so a raw
    id containing a filesystem/URL-reserved character (e.g. `?`) sanitizes instead of crashing
    the write or producing a link the browser reinterprets as a query string."""
    return "{}/{}/{}/".format(base, plugin, plugin_slug(item_id))


def topic_url(topic_id: str, base: str) -> str:
    return "{}/topic/{}/".format(base, topic_id)


def addon_url(plugin: str, base: str) -> str:
    return "{}/addon/{}/".format(base, plugin)


def prose_url(slug: str, base: str) -> str:
    return "{}/{}/".format(base, slug)


FAMILY_TOKEN = re.compile(r"%[A-Za-z_]+%")


def is_family_template(item_id: str) -> bool:
    return bool(FAMILY_TOKEN.search(item_id))


def family_slug(item_id: str) -> str:
    """The family page's slug: the `%TOKEN%` and any underscore left dangling beside it removed,
    the remainder slugged, with '-family' appended."""
    remainder = FAMILY_TOKEN.sub("", item_id)
    remainder = re.sub(r"_+", "_", remainder).strip("_")
    return plugin_slug(remainder) + "-family"


def family_url(plugin: str, item_id: str, base: str) -> str:
    return "{}/{}/{}/".format(base, plugin, family_slug(item_id))


def family_regex_source(item_id: str) -> str:
    """The families.json regex: derived from the id run through the SAME lowercase+slug rule a
    real variation's URL segment goes through, so the `%TOKEN%` placeholder (itself slugged, e.g.
    `%MOB%` -> `-mob-`) maps to `(.+)` at the matching position and the anchored result matches
    any concrete variation's slugged id (`%MOB%_SOUL_JAR` -> `^(.+)_soul_jar$`)."""
    slugged = plugin_slug(item_id.lower())
    placeholder = plugin_slug(FAMILY_TOKEN.search(item_id).group(0).lower())
    return "^" + re.escape(slugged).replace(re.escape(placeholder), "(.+)") + "$"


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
class ItemFamily:
    plugin: str
    addon_name: str
    template_id: str
    token: str
    name: str
    type_lines: List[str] = field(default_factory=list)
    description: List[str] = field(default_factory=list)
    stats: List[str] = field(default_factory=list)
    usage: List[str] = field(default_factory=list)
    regex: str = ""
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
    families: List[ItemFamily] = field(default_factory=list)
    collisions: List[str] = field(default_factory=list)

    def items_by_id(self) -> Dict[str, Item]:
        return {item.id: item for item in self.items}


class Claim(NamedTuple):
    url: str
    by: str


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

        items = []

        for entry in parse_items_yaml(text, repo.plugin, repo.name):
            if is_family_template(entry.id):
                site.families.append(ItemFamily(
                    plugin=entry.plugin, addon_name=entry.addon_name, template_id=entry.id,
                    token=FAMILY_TOKEN.search(entry.id).group(0),
                    name=entry.name, type_lines=entry.type_lines, description=entry.description,
                    stats=entry.stats, usage=entry.usage,
                    regex=family_regex_source(entry.id),
                    url=family_url(entry.plugin, entry.id, base)))
                continue

            entry.url = item_url(entry.plugin, entry.id, base)
            items.append(entry)

        site.items.extend(items)
        site.addons.append(Addon(plugin=repo.plugin, name=repo.name, items=items,
                                 url=addon_url(repo.plugin, base)))

    site.families.sort(key=lambda f: -len(FAMILY_TOKEN.sub("", f.template_id)))

    authored = parse_lines_yaml(sources.core_wiki_items or "")
    for item in site.items:
        item.wiki_lines = authored.get(item.id, [])

    mechanics = parse_lines_yaml(sources.core_mechanics or "")
    topic_items = parse_lines_yaml(sources.core_topic_items or "")
    claimed: Dict[str, Claim] = {}

    for topic in parse_topics_yaml(sources.core_topics or ""):
        topic.url = topic_url(topic.id, base)
        topic.body = mechanics.get(topic.id, [])
        topic.item_ids = topic_items.get(topic.id, [])

        if topic.page:
            if topic.page in prose:
                topic.prose_html = prose[topic.page]
                claimed[topic.page] = Claim(url=topic.url, by="topic '{}'".format(topic.id))
            else:
                site.collisions.append(
                    "topic '{}' names prose page '{}' which does not exist".format(topic.id, topic.page))

        site.topics.append(topic)

    by_slug = {}
    for item in site.items:
        by_slug.setdefault(page_slug(item.name), []).append(item)

    for slug, html in sorted(prose.items()):
        claim = claimed.get(slug)
        target = claim.url if claim else None
        claimant = claim.by if claim else None

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
