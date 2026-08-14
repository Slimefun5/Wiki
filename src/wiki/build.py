"""CLI entry point: fetch, merge, render, write, then assert the output is complete."""

import argparse
import html
import os
import re
import shutil
import sys

import markdown

from wiki import render
from wiki.fetch import MANIFEST_URL, MissingRequiredSource, fetch_sources, fetch_text
from wiki.model import build_site

GITHUB_WIKI = re.compile(r"https?://github\.com/Slimefun5/Slimefun5/wiki/([A-Za-z0-9_%\-]+)")
HREF = re.compile(r'href="([^"]+)"')
LOGO_SOURCE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "slimefun-icon.png")


def load_prose(pages_dir: str, base: str) -> dict:
    prose = {}

    for name in sorted(os.listdir(pages_dir)):
        if not name.endswith(".md"):
            continue

        with open(os.path.join(pages_dir, name), encoding="utf-8", errors="replace") as handle:
            text = GITHUB_WIKI.sub(lambda m: base + "/" + m.group(1) + "/", handle.read())

        prose[name[:-3]] = markdown.markdown(
            text, extensions=["tables", "fenced_code", "sane_lists"])

    return prose


def _write(out_dir: str, relative: str, content: str) -> None:
    path = os.path.join(out_dir, relative)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)


def _relative(url: str, base: str) -> str:
    """A path fragment with no leading slash, so os.path.join(out_dir, ...) never discards
    out_dir - including for the base root itself (url == base + "/")."""
    trimmed = url[len(base):].strip("/")
    return trimmed + "/index.html" if trimmed else "index.html"


def write_site(site, out_dir: str, base: str) -> int:
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)

    os.makedirs(out_dir, exist_ok=True)
    written = 0
    items_by_id = site.items_by_id()

    for item in site.items:
        assert item.url, "item {} has no url".format(item.id)
        _write(out_dir, _relative(item.url, base), render.render_item_page(item, base))
        written += 1

    for topic in site.topics:
        _write(out_dir, _relative(topic.url, base),
               render.render_topic_page(topic, items_by_id, base))
        written += 1

    families_by_plugin = {}
    for family in site.families:
        families_by_plugin.setdefault(family.plugin, []).append(family)
        _write(out_dir, _relative(family.url, base), render.render_family_page(family, base))
        written += 1

    for addon in site.addons:
        _write(out_dir, _relative(addon.url, base),
               render.render_addon_index(addon, base, families_by_plugin.get(addon.plugin)))
        written += 1

    guides = [p for p in site.prose if p.absorbed_by is None]

    for page in site.prose:
        content = (render.render_redirect(page.absorbed_by) if page.absorbed_by
                   else render.render_prose_page(page, base))
        _write(out_dir, _relative(page.url, base), content)
        written += 1

    _write(out_dir, "guides/index.html", render.render_guides_index(guides, base))
    _write(out_dir, "index.html", render.render_landing(site, base))
    _write(out_dir, "404.html", render.render_404_page(base))
    _write(out_dir, "assets/wiki.css", render.WIKI_CSS)
    _write(out_dir, "assets/search-index.json", render.search_index_json(site))
    _write(out_dir, "assets/families.json", render.families_json(site))
    _write(out_dir, ".nojekyll", "")

    if os.path.exists(LOGO_SOURCE):
        shutil.copy(LOGO_SOURCE, os.path.join(out_dir, "assets", "logo.png"))

    return written + 3


def check_links(out_dir: str, base: str) -> list:
    """Internal hrefs that no emitted file answers. Anchors, assets and absolute URLs are skipped."""
    dangling = []

    for root, _, files in os.walk(out_dir):
        for name in files:
            if not name.endswith(".html"):
                continue

            with open(os.path.join(root, name), encoding="utf-8") as handle:
                content = handle.read()

            for raw_href in HREF.findall(content):
                href = html.unescape(raw_href)

                if not href.startswith(base + "/") or "/assets/" in href:
                    continue

                target = os.path.join(out_dir, _relative(href.split("#")[0], base))

                if not os.path.exists(target) and href not in dangling:
                    dangling.append(href)

    return dangling


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--base", default="/wiki")
    parser.add_argument("--manifest", default=MANIFEST_URL)
    parser.add_argument("--core-ref", default=None)
    parser.add_argument("--strict-links", action="store_true",
                        help="Fail the build on any dangling internal link")
    parser.add_argument("--max-skipped", type=int, default=3,
                        help="Fail the build if more than this many addons are skipped")
    args = parser.parse_args(argv)

    base = args.base.rstrip("/")
    manifest_text = fetch_text(args.manifest)

    if manifest_text is None:
        print("error: manifest unavailable at " + args.manifest, file=sys.stderr)
        return 1

    try:
        sources = fetch_sources(manifest_text, core_ref=args.core_ref, max_skipped=args.max_skipped)
    except MissingRequiredSource as error:
        print("error: " + str(error), file=sys.stderr)
        return 1

    site = build_site(sources, load_prose(args.pages, base), base)

    for collision in site.collisions:
        print("warning: " + collision, file=sys.stderr)

    written = write_site(site, args.out, base)
    dangling = check_links(args.out, base)

    if dangling:
        # The 264 prose pages cross-link freely, including to pages that were never written, so a
        # dangling link is authored content rather than a generator bug and must not block a deploy.
        print("warning: {} dangling internal links, first 20: {}".format(
            len(dangling), ", ".join(dangling[:20])), file=sys.stderr)

        if args.strict_links:
            return 1

    print("wrote {} pages: {} items, {} families, {} topics, {} addons, {} prose".format(
        written, len(site.items), len(site.families), len(site.topics), len(site.addons),
        len(site.prose)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
