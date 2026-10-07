# cancho-www

Static front page for [cancho](https://github.com/alpibrusl/cancho), modelled on lex-www.
Plain HTML, no build step beyond copying files.

```sh
bash scripts/build_site.sh   # assemble _site/
```

`.github/workflows/pages.yml` deploys `_site/` to GitHub Pages on push to `main`.
Served by GitHub Pages at `alpibrusl.github.io/cancho-www/` (all links are relative).

Custom domain, once bought: add `echo "<domain>" > _site/CNAME` to `scripts/build_site.sh`, point the
apex at GitHub Pages (A records 185.199.108.153, .109.153, .110.153, .111.153), then add
`<link rel="canonical">` and `og:url` to `index.html`.
