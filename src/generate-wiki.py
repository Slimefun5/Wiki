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
  * an index lists every page, filterable by a small inline search.

The output is plain HTML with a ``.nojekyll`` marker, so GitHub Pages runs NO Jekyll build. ``--base`` is
the URL path the site is served under (the project-page prefix, e.g. ``/Wiki``); file paths omit it
because GitHub Pages adds the repository name to the URL itself, while link hrefs carry it.

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

# A line-art beaker (Slimefun's alchemy motif), drawn with currentColor so the header/favicon share it.
MARK = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
    'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<path d="M9 3h6M10 3v6L4.6 18.4A1.6 1.6 0 0 0 6 21h12a1.6 1.6 0 0 0 1.4-2.6L14 9V3"/>'
    '<path d="M7.5 14h9"/></svg>'
)

FAVICON = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' "
    "stroke='%2316a34a' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E"
    "%3Cpath d='M9 3h6M10 3v6L4.6 18.4A1.6 1.6 0 0 0 6 21h12a1.6 1.6 0 0 0 1.4-2.6L14 9V3'/%3E"
    "%3Cpath d='M7.5 14h9'/%3E%3C/svg%3E"
)

SITE_CSS = """\
:root{--bg:#fff;--fg:#18181b;--muted:#6b7280;--border:#e8e8ea;--code:#f4f4f5;--accent:#16a34a;--w:44rem}
@media(prefers-color-scheme:dark){:root{--bg:#0f1211;--fg:#e8eae9;--muted:#9aa0a6;--border:#242927;--code:#1a1e1c;--accent:#4ade80}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.65 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;-webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
.wrap,main,footer{max-width:var(--w);margin:0 auto;padding-left:1.25rem;padding-right:1.25rem}
header{border-bottom:1px solid var(--border)}
header .wrap{height:3.25rem;display:flex;align-items:center}
header a{display:flex;align-items:center;gap:.5rem;color:var(--fg);font-weight:650}
header a:hover{text-decoration:none}
header svg{width:1.3rem;height:1.3rem;color:var(--accent)}
main{padding-top:2.75rem;padding-bottom:4rem}
h1{font-size:1.95rem;line-height:1.2;letter-spacing:-.02em;margin:0 0 1rem;text-wrap:balance}
h2{font-size:1.3rem;letter-spacing:-.01em;margin:2.4rem 0 .8rem}
h3{font-size:1.08rem;margin:1.7rem 0 .5rem}
img{max-width:100%;border-radius:.5rem}
code{background:var(--code);padding:.15em .4em;border-radius:.3rem;font-size:.9em}
pre{background:var(--code);padding:1rem;border-radius:.6rem;overflow-x:auto}
pre code{background:none;padding:0}
blockquote{margin:1.2rem 0;padding:.1rem 0 .1rem 1rem;border-left:2px solid var(--accent);color:var(--muted)}
table{border-collapse:collapse;width:100%;margin:1.2rem 0;font-size:.95rem}
th,td{border-bottom:1px solid var(--border);padding:.55rem .7rem;text-align:left}
th{color:var(--muted);font-weight:600}
.back{display:inline-block;color:var(--muted);font-size:.9rem;margin-bottom:1.75rem}
.lede{color:var(--muted);margin:-.4rem 0 0}
.search{width:100%;margin:1.5rem 0 0;padding:.7rem .9rem;font:inherit;color:var(--fg);background:var(--bg);border:1px solid var(--border);border-radius:.6rem}
.search:focus{outline:2px solid var(--accent);outline-offset:1px;border-color:transparent}
.list{columns:2;column-gap:2.5rem;margin-top:1.5rem}
.list a{display:block;padding:.38rem 0;color:var(--fg);break-inside:avoid}
.list a:hover{color:var(--accent);text-decoration:none}
.none{color:var(--muted);display:none;margin-top:1.5rem}
footer{padding-top:2rem;padding-bottom:3rem;margin-top:1rem;border-top:1px solid var(--border);color:var(--muted);font-size:.85rem}
footer a{color:var(--muted);text-decoration:underline}
@media(max-width:640px){.list{columns:1}}
"""

INDEX_SCRIPT = """\
<script>
(function(){var q=document.getElementById('q'),g=document.getElementById('grid'),n=document.getElementById('none');
var a=[].slice.call(g.children);q.addEventListener('input',function(){var v=q.value.toLowerCase().trim(),c=0;
a.forEach(function(e){var m=e.getAttribute('data-name').indexOf(v)>-1;e.style.display=m?'':'none';if(m)c++;});
n.style.display=c?'none':'block';});})();
</script>
"""


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


def page_shell(title, base, inner_html):
    """Wrap page content in the shared site chrome (hairline header, content column, footer)."""
    safe_title = html.escape(title)
    return (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n"
        "<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"<title>{safe_title} · Slimefun Wiki</title>\n"
        f"<link rel=\"icon\" href=\"{FAVICON}\">\n"
        f"<link rel=\"stylesheet\" href=\"{base}/assets/style.css\">\n"
        "</head>\n<body>\n"
        f"<header><div class=\"wrap\"><a href=\"{base}/\">{MARK}<span>Slimefun Wiki</span></a></div></header>\n"
        f"<main>\n{inner_html}\n</main>\n"
        "<footer>Content licensed under the "
        "<a href=\"https://www.gnu.org/licenses/gpl-3.0.html\">GNU GPL v3.0</a> · "
        "<a href=\"https://slimefun5.github.io/builds/\">Builds</a> · "
        "<a href=\"https://github.com/Slimefun5\">GitHub</a></footer>\n"
        "</body>\n</html>\n"
    )


def render_content_page(title, body_html, base):
    """A single wiki topic: a back link, the title, then the rendered Markdown."""
    safe_title = html.escape(title)
    inner = (
        f"<a class=\"back\" href=\"{base}/\">← Back to index</a>\n"
        f"<h1>{safe_title}</h1>\n{body_html}"
    )
    return page_shell(title, base, inner)


def render_index(page_titles, base):
    """The landing page: a live-filterable list of every wiki topic."""
    links = "\n".join(
        f'<a data-name="{html.escape(t.lower())}" href="{base}/{page_slug(t)}/">{html.escape(t)}</a>'
        for t in sorted(page_titles)
    )
    inner = (
        "<h1>Slimefun Wiki</h1>\n"
        f"<p class=\"lede\">Browse every Slimefun item and mechanic — {len(page_titles)} pages.</p>\n"
        "<input id=\"q\" class=\"search\" type=\"search\" autocomplete=\"off\" "
        "placeholder=\"Search pages…\" aria-label=\"Search pages\">\n"
        f"<div id=\"grid\" class=\"list\">\n{links}\n</div>\n"
        "<p id=\"none\" class=\"none\">No pages match your search.</p>\n"
        f"{INDEX_SCRIPT}"
    )
    return page_shell("Slimefun Wiki", base, inner)


def to_html(markdown_text):
    return markdown.markdown(markdown_text, extensions=["tables", "fenced_code", "sane_lists"])


def emit_page(out_dir, slug, title, body_html, base):
    page_dir = os.path.join(out_dir, slug)
    os.makedirs(page_dir, exist_ok=True)
    with open(os.path.join(page_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_content_page(title, body_html, base))


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
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_index(page_titles, base))

    os.makedirs(os.path.join(out_dir, "assets"), exist_ok=True)
    with open(os.path.join(out_dir, "assets", "style.css"), "w", encoding="utf-8") as f:
        f.write(SITE_CSS)

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
