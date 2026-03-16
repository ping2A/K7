# Local dependencies for the editor

- **gifshot.min.js** — [gifshot](https://github.com/yahoo/gifshot) v0.4.5 (MIT), used for Export GIF. Served locally so the editor works without CDN access.

Serve the editor from this directory’s parent (e.g. `cd crates/k7-web && python3 -m http.server 8080`) so `deps/gifshot.min.js` loads correctly.
