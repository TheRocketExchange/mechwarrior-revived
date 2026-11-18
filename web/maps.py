"""Add map viewers to scenario setup and worked rules examples."""
from html import escape, unescape
from pathlib import Path
import re
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parent.parent
LABELS = {
    'first-contact-map': ('First Contact', '48 × 48 inches · 600 points'),
    'seize-and-hold-map': ('Seize and Hold', '48 × 48 inches · Skirmish / Standard'),
    'breakthrough-map': ('Breakthrough', '48 × 48 inches · Skirmish / Standard'),
    'hold-the-station-map': ('Hold the Station', '48 × 48 inches · Skirmish / Standard'),
    'movement-and-fire': ('Movement & shooting', 'Speed 8 · 2-inch grid'),
    'objective-control': ('Objective control', '3-inch control radius · 2-inch grid'),
    'pushing-and-recovery': ('Pushing & recovery', 'One activation per step'),
    'terrain-and-sight': ('Terrain & sight', 'Clear and blocked sight lines · 2-inch grid'),
    'terrain-movement': ('Moving through woods', '12 inches traveled · 16 inches of movement'),
    'smoke-generator': ('Smoke generator', '3-inch smoke radius · 2-inch grid'),
}


def metadata(stem):
    svg = ElementTree.parse(ROOT / 'scenarios/diagrams' / (stem+'.svg')).getroot()
    return svg.get('width'), svg.get('height'), svg.find('{http://www.w3.org/2000/svg}desc').text


def viewer(stem, alt=None, wide=False):
    title, subtitle = LABELS[stem]
    width,height,description = metadata(stem)
    source = 'diagrams/'+stem+'.svg'
    note = 'Distances are in inches.' if stem.endswith('-map') else 'Unit symbols mark centers, not base sizes.'
    if stem=='pushing-and-recovery': note='Vehicles and infantry squads.'
    choices=''
    if wide:
        wide_stem=stem.removesuffix('-map')+'-wide-map'
        wide_width,wide_height,wide_description=metadata(wide_stem)
        wide_alt=title+'. 72 × 48 inches. '+wide_description
        narrow_alt=title+'. '+subtitle+'. '+description
        choices=(f'<label class="map-size-control" hidden>Table<select data-map-size-select aria-label="Table size for {escape(title)}">'
                 f'<option value="{source}" data-width="{width}" data-height="{height}" data-alt="{escape(narrow_alt,quote=True)}" data-description="{subtitle}">48 × 48 inches</option>'
                 f'<option value="diagrams/{wide_stem}.svg" data-width="{wide_width}" data-height="{wide_height}" data-alt="{escape(wide_alt,quote=True)}" data-description="72 × 48 inches · Large / Grand">72 × 48 inches</option></select></label>'
                 f'<a href="diagrams/{wide_stem}.svg" data-map-wide>72 × 48 map</a>')
    return (f'<figure class="battle-map" data-map-title="{escape(title,quote=True)}" style="--map-width:{width}px">'
            f'<div class="battle-map-toolbar"><strong>{escape(title)}</strong><div class="battle-map-tools">{choices}'
            '<button type="button" data-map-zoom aria-pressed="false" hidden>Enlarge</button>'
            f'<a href="{source}" data-map-open target="_blank" rel="noopener">Open map ↗</a></div></div>'
            f'<div class="battle-map-viewport" tabindex="0" role="region" aria-label="{escape(title)} diagram">'
            f'<img src="{source}" alt="{escape(alt or description,quote=True)}" width="{width}" height="{height}" loading="lazy" decoding="async"></div>'
            f'<figcaption><span data-map-size>{escape(subtitle)}</span><span>{note}</span></figcaption></figure>')


def before_heading(body, anchor, figure):
    marker=f'<h2 id="{anchor}">'
    if marker not in body: raise ValueError(f'Missing diagram placement: {anchor}')
    return body.replace(marker,figure+marker,1)


def illustrate_maps(filename, body):
    # Keep the source Markdown usable on its own; enhance its linked diagrams.
    body=re.sub(r'<p><a href="diagrams/([^"/]+)\.svg"><img src="diagrams/\1\.svg" alt="([^"]*)"[^>]*></a></p>',
                lambda match:viewer(match[1],unescape(match[2]),wide=match[1] in
                    ('seize-and-hold-map','breakthrough-map','hold-the-station-map')),body)
    if filename=='readiness.html':
        body=before_heading(body,'recovery',viewer('pushing-and-recovery'))
    return body
