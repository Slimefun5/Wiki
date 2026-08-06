#!/usr/bin/env python3
"""Generate the static Slimefun wiki site (for slimefun5.github.io) from the wiki content pages.

The wiki content lives as one Markdown file per topic in ``pages/<Display-Name>.md``, with internal
links pointing at the GitHub wiki (``github.com/Slimefun5/Slimefun5/wiki/<Display-Name>``). This script
turns that into a GitHub Pages (Jekyll) site:

  * every content page is emitted at ``/wiki/<Display-Name>/`` (Jekyll renders the Markdown), with its
    GitHub-wiki links rewritten to site-relative ``/wiki/...`` links;
  * every Slimefun item id that has a matching page gets a redirect at ``/wiki/<plugin>/<id>/`` - the URL
    the in-game "View in Wiki" button builds (see core WikiLinks) - pointing at that content page;
  * an index lists every page.

GitHub Pages renders the Markdown itself, so no HTML conversion happens here.

Usage:
  python3 generate-wiki.py --pages pages --items <core items.yml> --out site [--plugin slimefun]
"""

import argparse
import os
import re
import shutil

# Links in the content point at the GitHub wiki; rewrite them to this site's /wiki/ paths.
GITHUB_WIKI = re.compile(r"https?://github\.com/Slimefun5/Slimefun5/wiki/([A-Za-z0-9_%\-]+)")
COLOR_CODE = re.compile(r"[&§][0-9a-fk-orA-FK-OR]")


def strip_color(text):
    return COLOR_CODE.sub("", text).strip().strip("'\"")


def parse_item_names(items_path):
    """Parse ``<ID>:\\n  name: '&x<Name>'`` into {id: display_name} without requiring PyYAML."""
    names = {}
    if not items_path or not os.path.exists(items_path):
        return names

    current_id = None
    with open(items_path, encoding="utf-8") as f:
        for line in f:
            stripped = line.rstrip("\n")
            top = re.match(r"^([A-Z0-9_]+):\s*$", stripped)
            if top:
                current_id = top.group(1)
                continue
            if current_id and re.match(r"^\s+name:\s*", stripped):
                value = stripped.split("name:", 1)[1].strip()
                names[current_id] = strip_color(value)
                current_id = None
    return names


def page_slug(display_name):
    """The wiki page slug for a display name, matching the existing ``pages/<slug>.md`` files."""
    return display_name.replace(" ", "-")


def rewrite_links(markdown):
    """Point GitHub-wiki links at this site instead (preserving any #anchor)."""
    return GITHUB_WIKI.sub(lambda m: "/wiki/" + m.group(1) + "/", markdown)


def emit_page(out_dir, slug, title, body):
    """Write one Jekyll content page at /wiki/<slug>/."""
    page_dir = os.path.join(out_dir, "wiki", slug)
    os.makedirs(page_dir, exist_ok=True)
    safe_title = title.replace('"', "'")
    front_matter = (
        "---\n"
        "layout: wiki\n"
        f'title: "{safe_title}"\n'
        f"permalink: /wiki/{slug}/\n"
        "---\n\n"
    )
    with open(os.path.join(page_dir, "index.md"), "w", encoding="utf-8") as f:
        f.write(front_matter + body)


def emit_redirect(out_dir, plugin, item_id, target_slug):
    """Write a meta-refresh redirect at /wiki/<plugin>/<id>/ pointing at the content page."""
    redirect_dir = os.path.join(out_dir, "wiki", plugin, item_id)
    os.makedirs(redirect_dir, exist_ok=True)
    target = f"/wiki/{target_slug}/"
    html = (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        f"<meta http-equiv=\"refresh\" content=\"0; url={target}\">"
        f"<link rel=\"canonical\" href=\"{target}\">"
        f"<title>Redirecting…</title></head><body>"
        f"Redirecting to <a href=\"{target}\">{target}</a>.</body></html>\n"
    )
    with open(os.path.join(redirect_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)


def write_scaffold(out_dir, page_titles):
    """Write the Jekyll config, layout, stylesheet and index."""
    with open(os.path.join(out_dir, "_config.yml"), "w", encoding="utf-8") as f:
        f.write(
            "title: Slimefun Wiki\n"
            "description: The official wiki for the Slimefun5 fork.\n"
            "markdown: kramdown\n"
            "exclude: [src, README.md, CONTRIBUTING.md, LICENSE]\n"
        )

    os.makedirs(os.path.join(out_dir, "_layouts"), exist_ok=True)
    with open(os.path.join(out_dir, "_layouts", "wiki.html"), "w", encoding="utf-8") as f:
        f.write(
            "<!doctype html>\n<html lang=\"en\">\n<head>\n"
            "<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
            "<title>{{ page.title }} · {{ site.title }}</title>\n"
            "<link rel=\"stylesheet\" href=\"/assets/style.css\">\n"
            "</head>\n<body>\n<header><a href=\"/wiki/\">{{ site.title }}</a></header>\n"
            "<main><h1>{{ page.title }}</h1>\n{{ content }}\n</main>\n"
            "<footer>Slimefun5 · content licensed under the GNU General Public License v3.0</footer>\n"
            "</body>\n</html>\n"
        )

    os.makedirs(os.path.join(out_dir, "assets"), exist_ok=True)
    with open(os.path.join(out_dir, "assets", "style.css"), "w", encoding="utf-8") as f:
        f.write(
            ":root{color-scheme:light dark}"
            "body{max-width:820px;margin:0 auto;padding:1.5rem;"
            "font-family:system-ui,sans-serif;line-height:1.6}"
            "header{font-weight:700;margin-bottom:1rem}"
            "header a{text-decoration:none}"
            "main img{max-width:100%}"
            "footer{margin-top:3rem;padding-top:1rem;border-top:1px solid #8884;"
            "font-size:.85rem;opacity:.7}"
            "table{border-collapse:collapse}td,th{border:1px solid #8884;padding:.3rem .6rem}\n"
        )

    lines = ["---", "layout: wiki", 'title: "Slimefun Wiki"', "permalink: /wiki/", "---", ""]
    lines.append("Browse every Slimefun item and mechanic:\n")
    for title in sorted(page_titles):
        lines.append(f"* [{title}](/wiki/{page_slug(title)}/)")
    os.makedirs(os.path.join(out_dir, "wiki"), exist_ok=True)
    with open(os.path.join(out_dir, "wiki", "index.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", required=True, help="Directory of <Display-Name>.md content pages")
    parser.add_argument("--items", help="Path to a core/addon items.yml for id->name mapping")
    parser.add_argument("--plugin", default="slimefun", help="Plugin slug for item redirect URLs")
    parser.add_argument("--out", required=True, help="Output site directory")
    args = parser.parse_args()

    if os.path.isdir(args.out):
        shutil.rmtree(args.out)
    os.makedirs(args.out, exist_ok=True)

    # Emit a content page for every wiki page, remembering the available slugs.
    page_titles = []
    available_slugs = set()
    for name in sorted(os.listdir(args.pages)):
        if not name.endswith(".md"):
            continue
        slug = name[:-3]
        title = slug.replace("-", " ")
        with open(os.path.join(args.pages, name), encoding="utf-8", errors="replace") as f:
            body = rewrite_links(f.read())
        emit_page(args.out, slug, title, body)
        page_titles.append(title)
        available_slugs.add(slug)

    # Emit /wiki/<plugin>/<id>/ redirects for every item id whose page exists.
    names = parse_item_names(args.items)
    redirects = 0
    for item_id, display_name in names.items():
        slug = page_slug(display_name)
        if slug in available_slugs:
            emit_redirect(args.out, args.plugin, item_id.lower(), slug)
            redirects += 1

    write_scaffold(args.out, page_titles)

    # No .nojekyll: we rely on GitHub Pages' Jekyll to render the Markdown pages.
    print(f"Generated {len(page_titles)} pages and {redirects} item redirects into {args.out}")


if __name__ == "__main__":
    main()
