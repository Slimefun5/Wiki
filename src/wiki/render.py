"""HTML rendering. No network, no filesystem: every function returns a string."""

import html
import json
import re
from typing import Dict, List

FAMILY_PLACEHOLDER = re.compile(r"%mob%", re.IGNORECASE)

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


def _attr(value: str) -> str:
    return html.escape(value, quote=True)


def page_shell(title: str, base: str, inner_html: str) -> str:
    safe = html.escape(title)
    base = _attr(base)
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
    items = "".join("<li>{}</li>".format(html.escape(line)) for line in lines if line)

    if not items:
        return ""

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
            _attr(base), _attr(item.plugin), html.escape(item.addon_name)),
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
        parts.append('<p><a href="{}">Read the full guide</a></p>\n'.format(_attr(item.prose_link)))

    return page_shell(item.name, base, "".join(parts))


def render_family_page(family, base: str) -> str:
    """The one real page emitted for an item-family template; %mob% renders as the literal
    words 'any mob' here (a concrete variation's own text is filled in dynamically by 404.html)."""
    replacement = "any mob"

    def sub(lines):
        return [FAMILY_PLACEHOLDER.sub(replacement, line) for line in lines]

    name = FAMILY_PLACEHOLDER.sub(replacement, family.name)
    parts = [
        '<a class="sf-back" href="{}/addon/{}/">\u2190 {}</a>\n'.format(
            _attr(base), _attr(family.plugin), html.escape(family.addon_name)),
        "<h1>{}<span class=\"sf-badge\">{}</span></h1>\n".format(
            html.escape(name), html.escape(family.addon_name)),
        _block(sub(family.type_lines)),
        _block(sub(family.description)),
        _block(sub(family.stats)),
        _block(sub(family.usage)),
    ]
    return page_shell(name, base, "".join(parts))


FAMILY_SCRIPT = """\
<script>
(function(){
function escapeHtml(s){var d=document.createElement('div');d.textContent=s;return d.innerHTML}
function block(lines,human){var items=(lines||[]).filter(Boolean).map(function(l){
return '<li>'+escapeHtml(l.replace(/%mob%/gi,human))+'</li>'}).join('');
return items?'<div class="sf-block"><ul>'+items+'</ul></div>':''}
var path=location.pathname,rest=path.indexOf(BASE)===0?path.slice(BASE.length):path,
segments=rest.replace(/^\\/+|\\/+$/g,'').split('/').filter(Boolean);
if(segments.length<2){return}
var plugin=segments[0],id=segments[1];
fetch(BASE+'/assets/families.json').then(function(r){return r.json()}).then(function(families){
for(var i=0;i<families.length;i++){var fam=families[i];
if(fam.plugin!==plugin){continue}
var match=id.match(new RegExp(fam.regex));
if(!match){continue}
var human=match[1].split('_').map(function(w){
return w.charAt(0).toUpperCase()+w.slice(1)}).join(' ');
document.getElementById('sf-404-main').innerHTML=
'<a class="sf-back" href="'+BASE+'/addon/'+fam.plugin+'/">\u2190 '+escapeHtml(fam.addon)+'</a>'+
'<h1>'+escapeHtml(fam.name.replace(/%mob%/gi,human))+
'<span class="sf-badge">'+escapeHtml(fam.addon)+'</span></h1>'+
block(fam.type,human)+block(fam.description,human)+block(fam.stats,human)+block(fam.usage,human);
return}
});})();
</script>
"""


def render_404_page(base: str) -> str:
    """GitHub Pages custom 404: resolves any concrete family-template variation URL client-side
    against families.json, since the unbounded variation set cannot be pre-generated as files."""
    inner = (
        '<div id="sf-404-main">'
        "<h1>Page not found</h1>\n"
        '<p class="sf-lede">That page does not exist.</p>\n'
        '<p><a href="{base}">Back to the index</a></p>\n'
        "</div>\n"
        '<script>var BASE="{raw_base}";</script>\n{script}'
    ).format(base=_attr(base + "/"), raw_base=base, script=FAMILY_SCRIPT)
    return page_shell("Page not found", base, inner)


def render_topic_page(topic, items_by_id: Dict[str, object], base: str) -> str:
    tiles = [items_by_id[item_id] for item_id in topic.item_ids if item_id in items_by_id]
    parts = [
        '<a class="sf-back" href="{}/">\u2190 Back to index</a>\n'.format(_attr(base)),
        "<h1>{}</h1>\n".format(html.escape(topic.title)),
        '<p class="sf-lede">{}</p>\n'.format(html.escape(topic.summary)),
        _paragraphs(topic.body),
    ]

    if topic.prose_html:
        parts.append(topic.prose_html)

    if tiles:
        links = "".join('<a href="{}">{}</a>'.format(_attr(i.url), html.escape(i.name)) for i in tiles)
        parts.append("<h2>Items in this topic</h2>\n<div class=\"sf-list\">{}</div>\n".format(links))

    return page_shell(topic.title, base, "".join(parts))


def render_prose_page(prose, base: str) -> str:
    inner = (
        '<a class="sf-back" href="{}/guides/">\u2190 All guides</a>\n'.format(_attr(base)) +
        "<h1>{}</h1>\n".format(html.escape(prose.title)) + prose.html
    )
    return page_shell(prose.title, base, inner)


def render_addon_index(addon, base: str, families=None) -> str:
    links = "".join('<a href="{}">{}</a>'.format(_attr(i.url), html.escape(i.name))
                    for i in sorted(addon.items, key=lambda i: i.name))
    inner = (
        '<a class="sf-back" href="{}/">\u2190 Back to index</a>\n'.format(_attr(base)) +
        "<h1>{}</h1>\n".format(html.escape(addon.name)) +
        '<p class="sf-lede">{} items</p>\n'.format(len(addon.items)) +
        '<div class="sf-list">{}</div>\n'.format(links)
    )

    if families:
        family_links = "".join(
            '<a href="{}">{}</a>'.format(_attr(f.url), html.escape(FAMILY_PLACEHOLDER.sub("any mob", f.name)))
            for f in sorted(families, key=lambda f: f.name))
        inner += "<h2>Item families</h2>\n<div class=\"sf-list\">{}</div>\n".format(family_links)

    return page_shell(addon.name, base, inner)


def render_guides_index(prose_pages, base: str) -> str:
    links = "".join('<a href="{}">{}</a>'.format(_attr(p.url), html.escape(p.title))
                    for p in sorted(prose_pages, key=lambda p: p.title))
    inner = (
        '<a class="sf-back" href="{}/">\u2190 Back to index</a>\n'.format(_attr(base)) +
        "<h1>Guides</h1>\n" +
        '<p class="sf-lede">{} guides</p>\n'.format(len(prose_pages)) +
        '<div class="sf-list">{}</div>\n'.format(links)
    )
    return page_shell("Guides", base, inner)


def render_landing(site, base: str) -> str:
    guides = [p for p in site.prose if p.absorbed_by is None]
    topics = "".join('<a href="{}">{}</a>'.format(_attr(t.url), html.escape(t.title)) for t in site.topics)
    cards = "".join(
        '<a class="sf-card" href="{}"><strong>{}</strong><br>'
        '<span class="sf-count">{} items</span></a>'.format(
            _attr(a.url), html.escape(a.name), len(a.items))
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
        '<script>var BASE="{raw_base}";</script>\n{script}'
    ).format(items=len(site.items), guides=len(guides), topics=topics, cards=cards,
             base=_attr(base), raw_base=base, script=SEARCH_SCRIPT)

    return page_shell("Slimefun Wiki", base, inner)


def render_redirect(target: str) -> str:
    attr = _attr(target)
    text = html.escape(target)
    return (
        '<!doctype html><html><head><meta charset="utf-8">'
        '<meta http-equiv="refresh" content="0; url={attr}">'
        '<link rel="canonical" href="{attr}">'
        "<title>Redirecting...</title></head><body>"
        'Redirecting to <a href="{attr}">{text}</a>.</body></html>\n'
    ).format(attr=attr, text=text)


def search_index(site) -> List[dict]:
    entries = [{"n": i.name, "u": i.url, "k": "item", "a": i.addon_name} for i in site.items]
    entries += [{"n": t.title, "u": t.url, "k": "topic", "a": ""} for t in site.topics]
    entries += [{"n": p.title, "u": p.url, "k": "guide", "a": ""}
                for p in site.prose if p.absorbed_by is None]
    entries += [{"n": FAMILY_PLACEHOLDER.sub("any mob", f.name), "u": f.url, "k": "family",
                "a": f.addon_name} for f in site.families]
    return entries


def search_index_json(site) -> str:
    return json.dumps(search_index(site), separators=(",", ":"))


def families_json(site) -> str:
    entries = [{
        "plugin": f.plugin, "regex": f.regex, "url": f.url, "addon": f.addon_name,
        "name": f.name, "type": f.type_lines, "description": f.description,
        "stats": f.stats, "usage": f.usage,
    } for f in site.families]
    return json.dumps(entries, separators=(",", ":"))
