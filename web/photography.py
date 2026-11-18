"""Place credited tabletop battle photographs in the HTML rulebook."""
from functools import lru_cache
from html import escape
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BANNER = "rocky-approach"

# These show other games using MechWarrior figures, not Revived rules or exact rosters.
PHOTOS = {
    "rules.html": [
        ("3-rounds-and-activation", "factory-battlefield"),
        ("7-combat", "close-quarters"),
        ("11-build-your-force", "spirit-cat-line"),
    ],
    "equipment.html": [("defense", "factory-defense")],
}


@lru_cache(maxsize=1)
def photographs():
    return json.loads((ROOT / "web/battle-photos/photos.json").read_text(encoding="utf-8"))


def photo_link(photo_id, banner=False):
    photo = photographs()[photo_id]
    source = 'battle-photos/' + photo['file']
    loading = 'fetchpriority="high"' if banner else 'loading="lazy"'
    return (f'<a class="battle-photo-link" href="{source}" style="--photo-position:{escape(photo["position"], quote=True)}">'
            f'<img src="{source}" alt="{escape(photo["alt"], quote=True)}" '
            f'width="{photo["width"]}" height="{photo["height"]}" decoding="async" {loading}></a>')


def credit(photo_id, css_class=""):
    photo = photographs()[photo_id]
    label = 'Photo: ' + escape(photo["credit"])
    if css_class == 'masthead-photo-credit':
        label = f'<span class="photo-credit-name">{label}</span><span class="photo-credit-short">Photo credit</span>'
    return (f'<a class="{css_class}" href="{escape(photo["source"], quote=True)}" aria-label="Photo: {escape(photo["credit"], quote=True)}">'
            f'{label}</a>')


def banner_html(filename):
    if filename != "index.html":
        return ''
    return ('<div class="masthead-photography">' + photo_link(BANNER, banner=True)
            + credit(BANNER, 'masthead-photo-credit') + '</div>')


def illustrate(filename, body):
    for anchor, photo_id in PHOTOS.get(filename, []):
        photo = photographs()[photo_id]
        figure = ('<figure class="rule-photo">' + photo_link(photo_id)
                  + f'<figcaption><span>{escape(photo["caption"])}</span>'
                  + credit(photo_id) + '</figcaption></figure>')
        if anchor is None:
            body = figure + body
        else:
            marker = f'<h2 id="{anchor}">'
            if marker not in body:
                raise ValueError(f'Missing photo placement: {filename}#{anchor}')
            end = body.index('</h2>', body.index(marker)) + len('</h2>')
            body = body[:end] + figure + body[end:]
    return body
