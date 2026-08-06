#!/usr/bin/env python3
"""Generate the static Slimefun wiki site from the wiki content pages.

The wiki content lives as one Markdown file per topic in ``pages/<Display-Name>.md``, with internal
links pointing at the GitHub wiki (``github.com/Slimefun5/Slimefun5/wiki/<Display-Name>``). This script
renders that into a fully static HTML site served from this repository's project page
(``slimefun5.github.io/Wiki/`` by default):

  * every content page is rendered to ``<base>/<Display-Name>/index.html`` (Markdown -> HTML here, so
    GitHub Pages serves it as-is), with its GitHub-wiki links rewritten to site-relative links;
  * every Slimefun item id that has a matching page gets a redirect at ``<base>/<plugin>/<id>/`` - the URL
    the in-game "View in Wiki" button builds (see core WikiLinks) - pointing at that content page;
  * an index lists every page.

The output is plain HTML with a ``.nojekyll`` marker, so GitHub Pages does NO Jekyll build (nothing to
fail on stray ``{{``/``{%`` sequences in the content). ``--base`` is the URL path the site is served
under (the project-page prefix, e.g. ``/Wiki``); file paths omit it because GitHub Pages adds the
repository name to the URL itself, while link hrefs carry it.

Usage:
  python3 generate-wiki.py --pages pages --items <core items.yml> --out site --base /Wiki
"""

import argparse
import html
import os
import re
import shutil

import markdown

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


def rewrite_links(markdown_text, base):
    """Point GitHub-wiki links at this site instead (preserving any #anchor)."""
    return GITHUB_WIKI.sub(lambda m: base + "/" + m.group(1) + "/", markdown_text)


def render_page(title, body_html, base):
    """Wrap rendered page HTML in the site shell."""
    safe_title = html.escape(title)
    return (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n"
        "<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"<title>{safe_title} · Slimefun Wiki</title>\n"
        f"<link rel=\"stylesheet\" href=\"{base}/assets/style.css\">\n"
        "</head>\n<body>\n"
        f"<header><a href=\"{base}/\">Slimefun Wiki</a></header>\n"
        f"<main><h1>{safe_title}</h1>\n{body_html}\n</main>\n"
        "<footer>Slimefun5 · content licensed under the GNU General Public License v3.0</footer>\n"
        "</body>\n</html>\n"
    )


def to_html(markdown_text):
    return markdown.markdown(markdown_text, extensions=["tables", "fenced_code", "sane_lists"])


def emit_page(out_dir, slug, title, body_html, base):
    page_dir = os.path.join(out_dir, slug)
    os.makedirs(page_dir, exist_ok=True)
    with open(os.path.join(page_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_page(title, body_html, base))


def emit_redirect(out_dir, plugin, item_id, target_slug, base):
    """Write a meta-refresh redirect at <base>/<plugin>/<id>/ pointing at the content page."""
    redirect_dir = os.path.join(out_dir, plugin, item_id)
    os.makedirs(redirect_dir, exist_ok=True)
    target = f"{base}/{target_slug}/"
    with open(os.path.join(redirect_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(
            "<!doctype html><html><head><meta charset=\"utf-8\">"
            f"<meta http-equiv=\"refresh\" content=\"0; url={target}\">"
            f"<link rel=\"canonical\" href=\"{target}\">"
            f"<title>Redirecting…</title></head><body>"
            f"Redirecting to <a href=\"{target}\">{target}</a>.</body></html>\n"
        )


def write_site_files(out_dir, page_titles, base):
    """Write the index, stylesheet and the .nojekyll marker (no Jekyll build)."""
    items = "\n".join(
        f'<li><a href="{base}/{page_slug(t)}/">{html.escape(t)}</a></li>' for t in sorted(page_titles)
    )
    index_body = f"<p>Browse every Slimefun item and mechanic:</p>\n<ul>\n{items}\n</ul>"
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_page("Slimefun Wiki", index_body, base))

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

    # .nojekyll: serve the pre-rendered HTML as-is; GitHub Pages runs no Jekyll build.
    with open(os.path.join(out_dir, ".nojekyll"), "w", encoding="utf-8") as f:
        f.write("")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", required=True, help="Directory of <Display-Name>.md content pages")
    parser.add_argument("--items", help="Path to a core/addon items.yml for id->name mapping")
    parser.add_argument("--plugin", default="slimefun", help="Plugin slug for item redirect URLs")
    parser.add_argument("--base", default="", help="URL path the site is served under, e.g. /Wiki")
    parser.add_argument("--out", required=True, help="Output site directory")
    args = parser.parse_args()

    base = args.base.rstrip("/")

    if os.path.isdir(args.out):
        shutil.rmtree(args.out)
    os.makedirs(args.out, exist_ok=True)

    page_titles = []
    available_slugs = set()
    for name in sorted(os.listdir(args.pages)):
        if not name.endswith(".md"):
            continue
        slug = name[:-3]
        title = slug.replace("-", " ")
        with open(os.path.join(args.pages, name), encoding="utf-8", errors="replace") as f:
            body_html = to_html(rewrite_links(f.read(), base))
        emit_page(args.out, slug, title, body_html, base)
        page_titles.append(title)
        available_slugs.add(slug)

    names = parse_item_names(args.items)
    redirects = 0
    for item_id, display_name in names.items():
        slug = page_slug(display_name)
        if slug in available_slugs:
            emit_redirect(args.out, args.plugin, item_id.lower(), slug, base)
            redirects += 1

    write_site_files(args.out, page_titles, base)

    print(f"Generated {len(page_titles)} pages and {redirects} item redirects into {args.out} (base '{base or '/'}')")


if __name__ == "__main__":
    main()
