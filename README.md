# Slimefun5 Wiki

This repository is both the **content source** and the **published website** for the Slimefun5 fork's wiki.

* **Web wiki:** https://slimefun5.github.io/Wiki/ — generated from the pages below and served via GitHub Pages.
* **Content:** one Markdown file per topic in [`pages/`](pages), kept in sync with the GitHub wiki at
  https://github.com/Slimefun5/Slimefun5/wiki

The in-game guide's "View in Wiki" button links to `https://slimefun5.github.io/Wiki/<plugin>/<id>`, which
redirects to the matching page.

## How it is built

[`src/generate-wiki.py`](src/generate-wiki.py) renders the content into a fully static HTML site (no
Jekyll — a `.nojekyll` marker tells GitHub Pages to serve it as-is):

* every `pages/<Display-Name>.md` is rendered to `/Wiki/<Display-Name>/`, with its GitHub-wiki links
  rewritten to site-relative links;
* every Slimefun item id (read from the core `items.yml`) that has a matching page gets a redirect at
  `/Wiki/<plugin>/<id>/` so the in-game links resolve;
* a `/Wiki/` index lists every page.

Requires the `markdown` package (`pip install markdown`).

```sh
python3 src/generate-wiki.py --pages pages --items items.yml --plugin slimefun --base /Wiki --out _src
```

## Deployment

[`.github/workflows/pages.yml`](.github/workflows/pages.yml) runs on every push to `stable` (and on demand):
it fetches the core `items.yml`, runs the generator, and publishes the static site to the `gh-pages` branch.
GitHub Pages serves that branch at https://slimefun5.github.io/Wiki/.

> One-time setup (org admin): enable GitHub Pages for this repository with **Source: Deploy from a branch →
> `gh-pages` / `/ (root)`**.

## Want to contribute?

See the guide: https://github.com/Slimefun5/Slimefun5/wiki/Expanding-the-Wiki

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE).
