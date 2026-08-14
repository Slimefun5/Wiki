"""Retrieval of every build input. The only module that touches the network."""

import json
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from urllib.error import URLError
from urllib.request import urlopen

MANIFEST_URL = "https://raw.githubusercontent.com/Slimefun5/manifest/main/addons.json"
ITEMS_PATH = "src/main/resources/languages/en/items.yml"
CORE_WIKI_PATHS = {
    "core_wiki_items": "core/src/main/resources/wiki/items.yml",
    "core_mechanics": "core/src/main/resources/wiki/mechanics.yml",
    "core_topics": "core/src/main/resources/wiki/topics.yml",
    "core_topic_items": "core/src/main/resources/wiki/topic-items.yml",
}
CORE_ITEMS_PATH = "core/" + ITEMS_PATH


class MissingRequiredSource(Exception):
    """Raised when a source the site cannot be built without is unavailable."""


@dataclass
class RepoRef:
    plugin: str
    name: str
    repo: str
    ref: str


@dataclass
class Sources:
    repos: List[RepoRef] = field(default_factory=list)
    items_yaml: Dict[str, str] = field(default_factory=dict)
    core_wiki_items: Optional[str] = None
    core_mechanics: Optional[str] = None
    core_topics: Optional[str] = None
    core_topic_items: Optional[str] = None
    skipped: List[str] = field(default_factory=list)


def raw_url(repo: str, ref: str, path: str) -> str:
    return "https://raw.githubusercontent.com/{}/{}/{}".format(repo, ref, path)


def fetch_text(url: str) -> Optional[str]:
    try:
        with urlopen(url, timeout=30) as response:
            return response.read().decode("utf-8")
    except (URLError, OSError, ValueError):
        return None


def _ref(entry: dict) -> RepoRef:
    plugin_name = entry.get("pluginName") or entry["repo"].split("/")[-1]
    return RepoRef(plugin=plugin_name.lower(), name=entry.get("name", plugin_name),
                   repo=entry["repo"], ref=entry.get("defaultBranch", "main"))


def parse_manifest(text: str) -> List[RepoRef]:
    """Core first, then addons. Libraries ship no items and are not part of the wiki."""
    manifest = json.loads(text)
    return [_ref(manifest["core"])] + [_ref(a) for a in manifest.get("addons", [])]


def _warn(message: str) -> None:
    print("warning: " + message, file=sys.stderr)


def fetch_sources(manifest_text: str, core_ref: Optional[str] = None, fetcher=fetch_text) -> Sources:
    repos = parse_manifest(manifest_text)
    core = repos[0]

    if core_ref:
        core = RepoRef(plugin=core.plugin, name=core.name, repo=core.repo, ref=core_ref)
        repos[0] = core

    sources = Sources(repos=[])

    core_items = fetcher(raw_url(core.repo, core.ref, CORE_ITEMS_PATH))

    if core_items is None:
        raise MissingRequiredSource(
            "core items.yml unavailable at {}@{}".format(core.repo, core.ref))

    sources.repos.append(core)
    sources.items_yaml[core.plugin] = core_items

    for attribute, path in CORE_WIKI_PATHS.items():
        text = fetcher(raw_url(core.repo, core.ref, path))

        if text is None:
            _warn("core resource {} unavailable, that section will be empty".format(path))

        setattr(sources, attribute, text)

    for repo in repos[1:]:
        text = fetcher(raw_url(repo.repo, repo.ref, ITEMS_PATH))

        if text is None:
            sources.skipped.append("{} has no {} at {}".format(repo.repo, ITEMS_PATH, repo.ref))
            continue

        sources.repos.append(repo)
        sources.items_yaml[repo.plugin] = text

    print("sources: {} repos, {} skipped".format(len(sources.repos), len(sources.skipped)))

    for skip in sources.skipped:
        _warn("skipped " + skip)

    return sources
