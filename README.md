# Slimefun5 Wiki

This repository is both the **content source** and the **published website** for the Slimefun5 fork's wiki.

* **Web wiki:** https://slimefun5.github.io/wiki/ - generated from the pages below and served via GitHub Pages.
* **Content:** one Markdown file per topic in [`pages/`](pages), kept in sync with the GitHub wiki at
  https://github.com/Slimefun5/Slimefun5/wiki

The in-game guide's "View in Wiki" button links to `https://slimefun5.github.io/wiki/<plugin>/<id>`, which
resolves directly to the matching page.

## How it is built

[`src/wiki/build.py`](src/wiki/build.py) fetches the manifest, core and addon repos, merges them with
the content in `pages/`, and renders a fully static HTML site (no Jekyll - a `.nojekyll` marker tells
GitHub Pages to serve it as-is):

* every `pages/<Display-Name>.md` is rendered to `/<base>/<Display-Name>/`, with its GitHub-wiki links
  rewritten to site-relative links;
* every Slimefun item id (read from every addon's `items.yml`) gets its own page at
  `/<base>/<plugin>/<id>/` so the in-game "View in Wiki" links resolve directly;
* item-family templates (ids containing a `%TOKEN%` placeholder, e.g. SoulJars' per-mob items) get one
  canonical family page plus a `404.html` fallback that resolves any concrete variation client-side;
* a `/<base>/` index lists every page, and dangling internal links are reported as warnings (or as a
  build failure with `--strict-links`).

Requires the `markdown` and `pyyaml` packages (`pip install markdown pyyaml`).

```sh
PYTHONPATH=src python3 -m wiki.build --pages pages --out _site --base /wiki
```

Flags: `--pages` (the `pages/` directory), `--out` (the output directory), `--base` (default `/wiki`),
`--manifest` (default the live `Slimefun5/manifest` addon list), `--core-ref` (override core's ref),
`--strict-links` (fail the build on any dangling internal link), `--max-skipped` (default `3`; fail the
build if more addons than this were unreachable, rather than silently publishing a degraded site).

## Deployment

[`.github/workflows/pages.yml`](.github/workflows/pages.yml) runs on every push to `stable` (and on demand):
it fetches the manifest plus every addon's `items.yml` and core's `wiki/*.yml`, runs the generator, and
publishes the static site to the `gh-pages` branch. GitHub Pages serves that branch at
https://slimefun5.github.io/wiki/.

> One-time setup (org admin): enable GitHub Pages for this repository with **Source: Deploy from a branch →
> `gh-pages` / `/ (root)`**.

## Want to contribute?

See the guide: https://github.com/Slimefun5/Slimefun5/wiki/Expanding-the-Wiki

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE).
