"""HTML rendering. No network, no filesystem: every function returns a string."""

import html
import json
from typing import Dict, List

WIKI_CSS = """\
.sf-lede{color:var(--sf-muted,#6b7280);margin:-.4rem 0 0}
.sf-badge{display:inline-block;padding:.15rem .5rem;border-radius:.35rem;background:var(--sf-code,#f4f4f5);
font-size:.8rem;color:var(--sf-muted,#6b7280);vertical-align:middle;margin-left:.5rem}
.sf-block{margin:1.1rem 0}
.sf-block li{list-style:none}
.sf-block ul{margin:0;padding:0}
.sf-search{width:100%;margin:1.5rem 0 0;padding:.7rem .9rem;font:inherit;color:inherit;
background:transparent;border:1px solid var(--sf-border,#e8e8ea);border-radius:.6rem}
.sf-list{columns:2;column-gap:2.5rem;margin-top:1.5rem}
.sf-list a{display:block;padding:.38rem 0;break-inside:avoid}
.sf-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(13rem,1fr));gap:1rem;margin-top:1.5rem}
.sf-card{border:1px solid var(--sf-border,#e8e8ea);border-radius:.6rem;padding:1rem}
.sf-card .sf-count{color:var(--sf-muted,#6b7280);font-size:.85rem}
.sf-none{color:var(--sf-muted,#6b7280);display:none;margin-top:1.5rem}
.sf-back{display:inline-block;font-size:.9rem;margin-bottom:1.75rem}
@media(max-width:640px){.sf-list{columns:1}}
"""

SEARCH_SCRIPT = """\
<script>
(function(){var q=document.getElementById('q'),g=document.getElementById('results'),
n=document.getElementById('none'),data=[];
fetch(BASE+'/assets/search-index.json').then(function(r){return r.json()}).then(function(j){data=j});
q.addEventListener('input',function(){var v=q.value.toLowerCase().trim();
if(!v){g.innerHTML='';n.style.display='none';return}
var hits=data.filter(function(e){return e.n.toLowerCase().indexOf(v)>-1}).slice(0,200);
g.innerHTML=hits.map(function(e){return '<a href="'+e.u+'">'+e.n+'<span class="sf-badge">'+
(e.a||e.k)+'</span></a>'}).join('');
n.style.display=hits.length?'none':'block';});})();
</script>
"""


def page_shell(title: str, base: str, inner_html: str) -> str:
    safe = html.escape(title)
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<title>{title} \u00b7 Slimefun Wiki</title>\n'
        '<link rel="icon" href="{base}/assets/logo.png">\n'
        '<link rel="stylesheet" href="{base}/assets/tokens.css">\n'
        '<link rel="stylesheet" href="{base}/assets/site.css">\n'
        '<link rel="stylesheet" href="{base}/assets/wiki.css">\n'
        '</head>\n<body>\n'
        '<header class="sf-header"><div class="sf-wrap"><a class="sf-brand" href="{base}/">'
        '<img src="{base}/assets/logo.png" alt="" width="24" height="24">'
        '<span>Slimefun Wiki</span></a></div></header>\n'
        '<main class="sf-wrap">\n{inner}\n</main>\n'
        '<footer class="sf-footer"><div class="sf-wrap">Content licensed under the '
        '<a href="https://www.gnu.org/licenses/gpl-3.0.html">GNU GPL v3.0</a> \u00b7 '
        '<a href="https://slimefun5.github.io/builds/">Builds</a> \u00b7 '
        '<a href="https://github.com/Slimefun5">GitHub</a></div></footer>\n'
        '</body>\n</html>\n'
    ).format(title=safe, base=base, inner=inner_html)


def _block(lines: List[str]) -> str:
    if not lines:
        return ""

    items = "".join("<li>{}</li>".format(html.escape(line)) for line in lines if line)
    return '<div class="sf-block"><ul>{}</ul></div>\n'.format(items)


def _paragraphs(lines: List[str]) -> str:
    paragraphs, current = [], []

    for line in lines:
        if line:
            current.append(html.escape(line))
        elif current:
            paragraphs.append(" ".join(current))
            current = []

    if current:
        paragraphs.append(" ".join(current))

    return "".join("<p>{}</p>\n".format(p) for p in paragraphs)


def render_item_page(item, base: str) -> str:
    parts = [
        '<a class="sf-back" href="{}/addon/{}/">\u2190 {}</a>\n'.format(
            base, item.plugin, html.escape(item.addon_name)),
        "<h1>{}<span class=\"sf-badge\">{}</span></h1>\n".format(
            html.escape(item.name), html.escape(item.addon_name)),
        _block(item.type_lines),
        _block(item.description),
        _block(item.stats),
        _block(item.usage),
        _paragraphs(item.wiki_lines),
    ]

    if item.prose_html:
        parts.append(item.prose_html)
    elif item.prose_link:
        parts.append('<p><a href="{}">Read the full guide</a></p>\n'.format(item.prose_link))

    return page_shell(item.name, base, "".join(parts))


def render_topic_page(topic, items_by_id: Dict[str, object], base: str) -> str:
    tiles = [items_by_id[item_id] for item_id in topic.item_ids if item_id in items_by_id]
    parts = [
        '<a class="sf-back" href="{}/">\u2190 Back to index</a>\n'.format(base),
        "<h1>{}</h1>\n".format(html.escape(topic.title)),
        '<p class="sf-lede">{}</p>\n'.format(html.escape(topic.summary)),
        _paragraphs(topic.body),
    ]

    if topic.prose_html:
        parts.append(topic.prose_html)

    if tiles:
        links = "".join('<a href="{}">{}</a>'.format(i.url, html.escape(i.name)) for i in tiles)
        parts.append("<h2>Items in this topic</h2>\n<div class=\"sf-list\">{}</div>\n".format(links))

    return page_shell(topic.title, base, "".join(parts))


def render_prose_page(prose, base: str) -> str:
    inner = (
        '<a class="sf-back" href="{}/guides/">\u2190 All guides</a>\n'.format(base) +
        "<h1>{}</h1>\n".format(html.escape(prose.title)) + prose.html
    )
    return page_shell(prose.title, base, inner)


def render_addon_index(addon, base: str) -> str:
    links = "".join('<a href="{}">{}</a>'.format(i.url, html.escape(i.name))
                    for i in sorted(addon.items, key=lambda i: i.name))
    inner = (
        '<a class="sf-back" href="{}/">\u2190 Back to index</a>\n'.format(base) +
        "<h1>{}</h1>\n".format(html.escape(addon.name)) +
        '<p class="sf-lede">{} items</p>\n'.format(len(addon.items)) +
        '<div class="sf-list">{}</div>\n'.format(links)
    )
    return page_shell(addon.name, base, inner)


def render_guides_index(prose_pages, base: str) -> str:
    links = "".join('<a href="{}">{}</a>'.format(p.url, html.escape(p.title))
                    for p in sorted(prose_pages, key=lambda p: p.title))
    inner = (
        '<a class="sf-back" href="{}/">\u2190 Back to index</a>\n'.format(base) +
        "<h1>Guides</h1>\n" +
        '<p class="sf-lede">{} guides</p>\n'.format(len(prose_pages)) +
        '<div class="sf-list">{}</div>\n'.format(links)
    )
    return page_shell("Guides", base, inner)


def render_landing(site, base: str) -> str:
    guides = [p for p in site.prose if p.absorbed_by is None]
    topics = "".join('<a href="{}">{}</a>'.format(t.url, html.escape(t.title)) for t in site.topics)
    cards = "".join(
        '<a class="sf-card" href="{}"><strong>{}</strong><br>'
        '<span class="sf-count">{} items</span></a>'.format(
            a.url, html.escape(a.name), len(a.items))
        for a in site.addons)

    inner = (
        "<h1>Slimefun Wiki</h1>\n"
        '<p class="sf-lede">{items} item pages and {guides} guides.</p>\n'
        '<input id="q" class="sf-search" type="search" autocomplete="off" '
        'placeholder="Search items and guides..." aria-label="Search items and guides">\n'
        '<div id="results" class="sf-list"></div>\n'
        '<p id="none" class="sf-none">Nothing matches your search.</p>\n'
        "<h2>Topics</h2>\n<div class=\"sf-list\">{topics}</div>\n"
        '<p><a href="{base}/guides/">All {guides} guides</a></p>\n'
        "<h2>Browse by addon</h2>\n<div class=\"sf-cards\">{cards}</div>\n"
        '<script>var BASE="{base}";</script>\n{script}'
    ).format(items=len(site.items), guides=len(guides), topics=topics, cards=cards,
             base=base, script=SEARCH_SCRIPT)

    return page_shell("Slimefun Wiki", base, inner)


def render_redirect(target: str) -> str:
    return (
        '<!doctype html><html><head><meta charset="utf-8">'
        '<meta http-equiv="refresh" content="0; url={target}">'
        '<link rel="canonical" href="{target}">'
        "<title>Redirecting...</title></head><body>"
        'Redirecting to <a href="{target}">{target}</a>.</body></html>\n'
    ).format(target=target)


def search_index(site) -> List[dict]:
    entries = [{"n": i.name, "u": i.url, "k": "item", "a": i.addon_name} for i in site.items]
    entries += [{"n": t.title, "u": t.url, "k": "topic", "a": ""} for t in site.topics]
    entries += [{"n": p.title, "u": p.url, "k": "guide", "a": ""}
                for p in site.prose if p.absorbed_by is None]
    return entries


def search_index_json(site) -> str:
    return json.dumps(search_index(site), separators=(",", ":"))
