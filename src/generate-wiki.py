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


# A book octicon, used as the header mark and (as a data URI) the favicon. Kept inline so the site has
# no external asset dependency for its chrome.
LOGO_SVG = (
    '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M0 1.75A.75.75 0 0 1 .75 1h4.253c1.227 0 '
    '2.317.59 3 1.501A3.743 3.743 0 0 1 11.006 1h4.245a.75.75 0 0 1 .75.75v10.5a.75.75 0 0 1-.75.75h-4.507a2.25 '
    '2.25 0 0 0-1.591.659l-.622.621a.75.75 0 0 1-1.06 0l-.622-.621A2.25 2.25 0 0 0 5.258 13H.75a.75.75 0 0 '
    '1-.75-.75Zm7.251 10.324.004-5.073-.002-2.253A2.25 2.25 0 0 0 5.003 2.5H1.5v9h3.757a3.75 3.75 0 0 1 1.994.574ZM8.755 '
    '4.75l-.004 7.322a3.752 3.752 0 0 1 1.992-.572H14.5v-9h-3.495a2.25 2.25 0 0 0-2.25 2.25Z"/></svg>'
)

FAVICON = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='%2376d1ff'"
    "%3E%3Cpath d='M0 1.75A.75.75 0 0 1 .75 1h4.253c1.227 0 2.317.59 3 1.501A3.743 3.743 0 0 1 11.006 "
    "1h4.245a.75.75 0 0 1 .75.75v10.5a.75.75 0 0 1-.75.75h-4.507a2.25 2.25 0 0 0-1.591.659l-.622.621a.75.75 "
    "0 0 1-1.06 0l-.622-.621A2.25 2.25 0 0 0 5.258 13H.75a.75.75 0 0 1-.75-.75Z'/%3E%3C/svg%3E"
)


def page_shell(title, base, inner_html):
    """Wrap page content in the shared Slimefun5 site chrome (header bar, panel, footer)."""
    safe_title = html.escape(title)
    return (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n"
        "<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"<title>{safe_title} · Slimefun Wiki</title>\n"
        f"<link rel=\"icon\" href=\"{FAVICON}\">\n"
        "<link href=\"https://fonts.googleapis.com/css?family=Noto+Sans:400,700\" rel=\"stylesheet\">\n"
        f"<link rel=\"stylesheet\" href=\"{base}/assets/style.css\">\n"
        "</head>\n<body>\n"
        "<header class=\"site-header\"><div class=\"inner\">"
        f"<a class=\"brand\" href=\"{base}/\">{LOGO_SVG}<span>Slimefun Wiki</span></a>"
        "</div></header>\n"
        f"<main>\n{inner_html}\n</main>\n"
        "<footer>Slimefun5 · content licensed under the "
        "<a href=\"https://www.gnu.org/licenses/gpl-3.0.html\">GNU General Public License v3.0</a> · "
        "<a href=\"https://slimefun5.github.io/builds/\">Builds</a> · "
        "<a href=\"https://github.com/Slimefun5\">GitHub</a></footer>\n"
        "</body>\n</html>\n"
    )


def render_content_page(title, body_html, base):
    """A single wiki topic: a back link plus the rendered Markdown in a prose panel."""
    safe_title = html.escape(title)
    inner = (
        f"<a class=\"back\" href=\"{base}/\">← All pages</a>\n"
        f"<article class=\"panel prose\">\n<h1>{safe_title}</h1>\n{body_html}\n</article>"
    )
    return page_shell(title, base, inner)


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


INDEX_SCRIPT = """
<script>
(function(){
  var q=document.getElementById('q'),grid=document.getElementById('grid'),none=document.getElementById('none');
  var cards=[].slice.call(grid.querySelectorAll('.card'));
  q.addEventListener('input',function(){
    var v=q.value.toLowerCase().trim(),n=0;
    cards.forEach(function(c){var m=c.getAttribute('data-name').indexOf(v)!==-1;c.style.display=m?'':'none';if(m)n++;});
    none.style.display=n?'none':'block';
  });
})();
</script>
"""


def render_index(page_titles, base):
    """The landing page: a live-filterable grid of every wiki topic."""
    cards = "\n".join(
        f'<a class="card" data-name="{html.escape(t.lower())}" href="{base}/{page_slug(t)}/">{html.escape(t)}</a>'
        for t in sorted(page_titles)
    )
    inner = (
        "<div class=\"index-head\">"
        "<h1>Slimefun Wiki</h1>"
        f"<p>Browse every Slimefun item and mechanic — {len(page_titles)} pages.</p>"
        "</div>\n"
        "<input id=\"q\" class=\"search\" type=\"search\" autocomplete=\"off\" "
        "placeholder=\"Search pages…\" aria-label=\"Search pages\">\n"
        f"<div id=\"grid\" class=\"grid\">\n{cards}\n</div>\n"
        "<p id=\"none\" class=\"no-results\">No pages match your search.</p>"
        f"{INDEX_SCRIPT}"
    )
    return page_shell("Slimefun Wiki", base, inner)


SITE_CSS = """\
:root{
  --header:#1a1a1a;--header-text:#fafafa;
  --background:#343a40;--panel:#232426;
  --border:#2b2f32;--shadow:#20292f;
  --text:#e2e2e2;--muted:#9ba6aa;
  --link:#76d1ff;--link-hover:#00a9ff;--secondary-link:#6bbfe9;
  --table-primary:#363b3f;--table-secondary:#2d3338;--table-head:#222325;
  --code-bg:#1c1e20;
}
*{box-sizing:border-box}
html,body{margin:0;background:var(--background);color:var(--text);
  font-family:'Noto Sans',system-ui,-apple-system,Segoe UI,sans-serif;line-height:1.65}
a{color:var(--link);text-decoration:none}
a:hover{color:var(--link-hover);text-decoration:underline}

.site-header{position:sticky;top:0;z-index:10;background:var(--header);
  border-bottom:1px solid #000;box-shadow:0 2px 6px var(--shadow)}
.site-header .inner{max-width:960px;margin:0 auto;padding:.7rem 1.2rem;display:flex;align-items:center}
.site-header .brand{display:flex;align-items:center;gap:.55rem;color:var(--header-text);
  font-weight:700;font-size:1.15rem}
.site-header .brand:hover{text-decoration:none}
.site-header svg{width:24px;height:24px;fill:var(--link)}

main{max-width:960px;margin:1.6rem auto;padding:0 1.2rem}
.panel{background:var(--panel);border:1px solid var(--border);border-radius:10px;
  box-shadow:0 3px 8px var(--shadow);padding:1.6rem 1.9rem}

.back{display:inline-block;margin-bottom:1rem;color:var(--muted);font-size:.9rem}
.back:hover{color:var(--link)}

.prose h1{margin:.1rem 0 1rem;font-size:1.9rem;border-bottom:1px solid var(--border);padding-bottom:.4rem}
.prose h2{margin:2rem 0 .8rem;font-size:1.4rem;border-bottom:1px solid var(--border);padding-bottom:.3rem}
.prose h3{margin:1.5rem 0 .6rem;font-size:1.15rem}
.prose p,.prose li{color:var(--text)}
.prose img{max-width:100%;border-radius:6px}
.prose code{background:var(--code-bg);padding:.15rem .4rem;border-radius:4px;
  font-family:SFMono-Regular,Consolas,monospace;font-size:.9em}
.prose pre{background:var(--code-bg);padding:1rem;border-radius:8px;overflow-x:auto;border:1px solid var(--border)}
.prose pre code{background:none;padding:0}
.prose blockquote{margin:1rem 0;padding:.5rem 1rem;border-left:3px solid var(--link);
  background:#ffffff08;color:var(--muted)}
.prose table{border-collapse:collapse;width:100%;margin:1rem 0;display:block;overflow-x:auto}
.prose th{background:var(--table-head);text-align:left}
.prose td,.prose th{border:1px solid var(--border);padding:.5rem .8rem}
.prose tr:nth-child(odd) td{background:var(--table-secondary)}
.prose tr:nth-child(even) td{background:var(--table-primary)}
.prose ul,.prose ol{padding-left:1.4rem}
.prose a{color:var(--link)}

.index-head h1{margin:.2rem 0 .3rem;font-size:1.9rem}
.index-head p{margin:0;color:var(--muted)}
.search{width:100%;margin:1.2rem 0;padding:.7rem 1rem;font-size:1rem;background:var(--panel);
  border:1px solid var(--border);border-radius:8px;color:var(--text)}
.search:focus{outline:none;border-color:var(--link)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:.7rem}
.card{display:block;padding:.8rem 1rem;background:var(--panel);border:1px solid var(--border);
  border-radius:8px;color:var(--text);font-weight:600;transition:border-color .12s,transform .12s,color .12s}
.card:hover{border-color:var(--link);color:var(--link);text-decoration:none;transform:translateY(-1px)}
.no-results{color:var(--muted);padding:1rem 0;display:none}

footer{max-width:960px;margin:2.5rem auto 2rem;padding:1.2rem;color:var(--muted);
  font-size:.85rem;border-top:1px solid var(--border);text-align:center}
footer a{color:var(--secondary-link)}
"""


def write_site_files(out_dir, page_titles, base):
    """Write the index, stylesheet and the .nojekyll marker (no Jekyll build)."""
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_index(page_titles, base))

    os.makedirs(os.path.join(out_dir, "assets"), exist_ok=True)
    with open(os.path.join(out_dir, "assets", "style.css"), "w", encoding="utf-8") as f:
        f.write(SITE_CSS)

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
