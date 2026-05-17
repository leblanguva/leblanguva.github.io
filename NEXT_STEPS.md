# Next steps — your homepage

The site is up and configured with a minimal placeholder. Here's what to do next, in order of payoff.

## 1. Add a headshot
Drop a square PNG (~500×500 px) into `images/profile.png`, replacing the placeholder. Commit and push and it appears in the sidebar.

## 2. Fill in the parts left blank in `_config.yml`
Open `_config.yml` and search for `TODO:`. The placeholders worth filling:
- `googlescholar` — your Google Scholar profile URL
- `orcid` — your ORCID URL
- `bluesky` — handle if you have one
- LinkedIn / Twitter — uncomment the lines under "Social media" and add usernames

## 3. Replace the placeholder about page
Edit `_pages/about.md` — that's the landing page. Write whatever bio you want.

## 4. Add publications
The publications page builds from `_publications/` — one Markdown file per paper. The repo includes example files; copy one, rename it, and edit. Each file has YAML frontmatter (title, venue, date, paperurl) and a Markdown abstract.

For a bulk import, you can edit `markdown_generator/publications.tsv` and run the included Jupyter notebook to generate all the files at once — useful if you have a CV-style list ready to paste.

## 5. CV
Edit `_pages/cv.md` directly (it's the auto-rendered HTML CV), or drop a PDF into `files/` and link to it from your about page.

## 6. Top navigation
`_data/navigation.yml` controls what shows up in the top menu. Remove anything you don't want (Portfolio? Blog? Talks?).

## 7. Trim the example content
Delete the example files in `_posts/`, `_talks/`, `_publications/`, `_portfolio/`, `_teaching/` once you have your own to avoid them showing up on the live site. Or just leave them and override one at a time.

## 8. Where the live site lives
After the first push, your site builds at: https://leblanguva.github.io. First build takes ~1 minute. Each subsequent push re-builds in ~30 seconds. If something looks broken, check the Actions tab of the repo on github.com — the Pages build log will be there.
