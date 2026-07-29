# AdPilot legal site

This folder contains a production-quality static legal website for AdPilot intended for Cloudflare Pages direct upload.

## Files

- index.html — home page
- privacy/index.html — privacy policy
- terms/index.html — terms of service
- data-deletion/index.html — deletion instructions
- styles.css — shared styling
- scripts.js — minimal mobile navigation behavior
- assets/ — brand mark and favicon
- robots.txt — crawler instructions
- sitemap.xml — sitemap
- 404.html — custom not-found page
- _headers — Cloudflare Pages security headers

## Local preview

Open the folder in a browser, or serve it locally with any static server such as:

```bash
python -m http.server 8000
```

Then visit:

- http://localhost:8000/
- http://localhost:8000/privacy/
- http://localhost:8000/terms/
- http://localhost:8000/data-deletion/

## Cloudflare Pages deployment

1. Create a new Pages project in the Cloudflare dashboard.
2. Choose Direct Upload.
3. Upload this folder as a ZIP or drag and drop the folder contents.
4. Set the project name to adpilot-legal.
5. Deploy.

## Important note

The content is a technical draft and should be reviewed by qualified legal counsel before production launch. The operator must confirm the legal business name, business address, contacts, effective date, retention period, and hosting providers before final publication.
