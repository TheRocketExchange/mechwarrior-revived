"""Flash-era strategy-game art for measured battlefields and worked examples.

Board coordinates are inches from the southwest corner. Woods have curved
edges inside their measured bounds; textures and tokens add no obstacles.
"""
from html import escape

INK, MUTED = "#30392f", "#59614f"
BLUE, RED, GOLD = "#346b9e", "#b5523c", "#946416"
PAPER, GROUND, GRID = "#eee9d8", "#b9c18c", "#899263"
TERRAIN = {"woods": ("#8ca661", "#35452f", "Woods"),
           "rubble": ("#c4ae83", "#514a37", "Rubble"),
           "blocking": ("#899397", "#343d40", "Blocking"),
           "fieldworks": ("#cbb486", "#594832", "Fieldworks"),
           "water": ("#83b0be", "#3d626b", "Shallow water")}


def text(x, y, value, size=18, anchor="start", fill=INK, weight="normal", extra=""):
    return f'<text x="{x:g}" y="{y:g}" font-size="{size}" text-anchor="{anchor}" fill="{fill}" font-weight="{weight}" {extra}>{escape(str(value))}</text>'


def rect(x, y, w, h, fill, stroke="none", extra=""):
    return f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="{fill}" stroke="{stroke}" {extra}/>'


def woods_curves(x, y, width, height):
    """Shared SVG/PDF outline. Opposite halves match under a half-turn.

    The middle horizontal crossing spans the full width, preserving the
    measured four-inch woodland segment in the movement example.
    """
    upper = [(0, .39, .09, .39, .07, .30),
             (.02, .18, .18, .08, .29, .13),
             (.36, .17, .37, 0, .5, 0),
             (.63, 0, .65, .12, .74, .10),
             (.88, .04, .99, .16, .93, .29),
             (.90, .38, 1, .41, 1, .5)]
    curves = upper + [tuple(1-value for value in curve) for curve in upper]
    return [tuple((x + value*width) if i % 2 == 0 else (y + value*height)
                  for i, value in enumerate(curve)) for curve in curves]


def woods_shape(width, height):
    path = f'M0 {height/2:g}' + ''.join(
        'C' + ' '.join(f'{value:g}' for value in curve)
        for curve in woods_curves(0, 0, width, height)) + 'Z'
    return f'<path d="{path}" fill="url(#woods)" stroke="{TERRAIN["woods"][1]}" stroke-width="2.5" stroke-linejoin="round"/>'


def line(x1, y1, x2, y2, color=MUTED, width=2, extra=""):
    return f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" stroke="{color}" stroke-width="{width}" {extra}/>'


def circle(x, y, radius, fill="none", stroke=MUTED, extra=""):
    return f'<circle cx="{x:g}" cy="{y:g}" r="{radius:g}" fill="{fill}" stroke="{stroke}" {extra}/>'


def badge(x, y, value, fill=PAPER, color=INK, size=15, width=None):
    width = width or max(34, len(str(value)) * size * .61 + 14)
    return (rect(x-width/2+2, y-size+3, width, size+9, INK, extra='opacity=".25" rx="2"')
            + rect(x-width/2, y-size+1, width, size+9, fill, color, 'stroke-width="2" rx="2"')
            + text(x, y+2, value, size, "middle", color, "bold"))


DEFS = '''<defs>
<pattern id="ground" patternUnits="userSpaceOnUse" width="84" height="68"><rect width="84" height="68" fill="#b9c18c"/><path d="M10 18l-3 -5m3 5l4 -6M60 51l-2 -5m2 5l4 -3" fill="none" stroke="#9ca971" stroke-width="2" stroke-linecap="round"/><path d="M35 38h6M70 12h4" stroke="#a8b57a" stroke-width="2"/></pattern>
<pattern id="woods" patternUnits="userSpaceOnUse" width="44" height="42"><rect width="44" height="42" fill="#8ca661"/><ellipse cx="25" cy="29" rx="16" ry="10" fill="#6e874d"/><path d="M20 26v10h6V25" fill="#8b7045" stroke="#35452f" stroke-width="2"/><path d="M9 24C2 17 8 10 14 11C14 2 28 1 31 10C41 8 45 22 36 26C31 33 23 30 20 28C14 31 9 29 9 24Z" fill="#5d8c48" stroke="#35452f" stroke-width="2.5" stroke-linejoin="round"/><path d="M12 18Q11 13 18 14Q20 7 27 12" fill="none" stroke="#94b66a" stroke-width="3" stroke-linecap="round"/></pattern>
<pattern id="rubble" patternUnits="userSpaceOnUse" width="45" height="40"><rect width="45" height="40" fill="#c4ae83"/><path d="M6 15L12 5L24 8L27 20L17 25L6 22Z M28 29L33 20L42 24L41 35L29 36Z" fill="#958d76" stroke="#514a37" stroke-width="2.5" stroke-linejoin="round"/><path d="M9 14L14 9L22 12M31 29L35 25L39 27" fill="none" stroke="#c6c3a8" stroke-width="3"/><path d="M4 32l4 -1M34 9l3 3" stroke="#806e4f" stroke-width="2"/></pattern>
<pattern id="blocking" patternUnits="userSpaceOnUse" width="32" height="28"><rect width="32" height="28" fill="#899397"/><path d="M0 27H32M31 0V28" stroke="#576367" stroke-width="2"/><path d="M2 2H28" stroke="#b5bdbb" stroke-width="2"/></pattern>
<pattern id="fieldworks" patternUnits="userSpaceOnUse" width="40" height="32"><rect width="40" height="32" fill="#cbb486"/><path d="M0 10H12V23H28V10H40" fill="none" stroke="#594832" stroke-width="12" stroke-linejoin="round"/><path d="M0 10H12V23H28V10H40" fill="none" stroke="#9a8158" stroke-width="6" stroke-linejoin="round"/><path d="M0 5H9M16 28H25M32 5H40" stroke="#eee0ad" stroke-width="3" stroke-linecap="round"/><path d="M5 6v8M17 19v8M33 6v8" stroke="#594832" stroke-width="2"/></pattern>
<pattern id="water" patternUnits="userSpaceOnUse" width="40" height="30"><rect width="40" height="30" fill="#83b0be"/><path d="M4 10Q9 5 14 10T24 10M22 24Q27 19 32 24" fill="none" stroke="#c2dee0" stroke-width="3" stroke-linecap="round"/></pattern>
<marker id="move-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0L10 5L0 10Z" fill="#346b9e"/></marker>
<marker id="sight-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0L10 5L0 10Z" fill="#946416"/></marker>
<marker id="measure-arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 1L7 4L0 7" fill="none" stroke="#30392f" stroke-width="1.4"/></marker>
</defs>'''


def save(path, title, subtitle, body, width, height, description, tag="FIELD GUIDE"):
    header = [rect(0, 0, width, height, PAPER), rect(0, 5, width, 82, "#b7b39e"),
              rect(0, 0, width, 82, "#4b6171", INK, 'stroke-width="4"'),
              line(0, 4, width, 4, '#8198a1', 4),
              text(28, 25, tag, 12, fill="#d5dfce", weight="bold", extra='letter-spacing="1"'),
              text(29, 63, title, 29, fill=INK, weight="bold"),
              text(28, 60, title, 29, fill="#fff6d9", weight="bold"),
              text(28, 111, subtitle, 18, fill=MUTED)]
    footer = [line(28, height-43, width-28, height-43, "#aaa991", 2),
              text(28, height-20, "MECHWARRIOR REVIVED", 12, fill=MUTED, weight="bold"),
              text(width-28, height-20, "SETUP & RULES EXAMPLES", 11, "end", MUTED)]
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:g}" height="{height:g}" viewBox="0 0 {width:g} {height:g}" role="img" aria-labelledby="title desc">'
           f'<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>'
           + DEFS + '<g font-family="Arial, Helvetica, sans-serif">' + ''.join(header+body+footer) + '</g></svg>\n')
    path.write_text(svg, encoding="utf-8")


class Board:
    def __init__(self, width, depth, left, top, scale, grid=6, axes=True):
        self.width, self.depth, self.left, self.top, self.scale = width, depth, left, top, scale
        self.grid, self.axes = grid, axes
        self.zones, self.features, self.overlay, self.labels = [], [], [], []

    def x(self, value): return self.left + value*self.scale
    def y(self, value): return self.top + (self.depth-value)*self.scale

    def zone(self, zone):
        low, high = zone['low'], zone['high']
        blue = zone['side']=='blue'
        color = BLUE if blue else RED
        self.zones.append(rect(self.left, self.y(high), self.width*self.scale, (high-low)*self.scale,
                               '#9eb9b8' if blue else '#d4ad88', extra=f'data-zone="{zone["id"]}" data-low="{low}" data-high="{high}" fill-opacity=".7"'))
        for value in (low,high):
            if value not in (0,self.depth):
                self.zones.append(line(self.left,self.y(value),self.x(self.width),self.y(value),color,2,'stroke-dasharray="8 5"'))
        # Dimension arrows supply the limits on scenario maps.
        label_y = self.y((low+high)/2)
        if high-low>8: label_y=self.y(high-1.8)
        if 'label_y' in zone: label_y=self.y(zone['label_y'])
        self.overlay.append(badge(self.x(self.width/2), label_y+3, zone['name'], PAPER,color,15))

    def terrain(self, feature):
        kind, ident = feature['kind'], feature['id']
        px, py = self.x(feature['x']), self.y(feature['y']+feature['depth'])
        w,h = feature['width']*self.scale, feature['depth']*self.scale
        if kind == 'woods':
            self.features.append(f'<svg x="{px:g}" y="{py:g}" width="{w:g}" height="{h:g}" '
                                 f'viewBox="0 0 {w:g} {h:g}" overflow="visible" '
                                 f'data-terrain="{ident}" data-kind="woods">'
                                 + woods_shape(w, h) + '</svg>')
        else:
            self.features.append(rect(px,py,w,h,f'url(#{kind})',TERRAIN[kind][1],
                                      f'stroke-width="2.5" data-terrain="{ident}" data-kind="{kind}"'))
        if kind=='blocking' and min(w,h)>24:
            self.features += [rect(px+6,py+8,w-10,h-11,'#596568'),
                              rect(px+4,py+4,w-12,h-12,'#a4afac',INK,'stroke-width="2.5"'),
                              line(px+7,py+7,px+w-12,py+7,'#d6dbca',3),
                              rect(px+w*.3,py+h*.52,w*.35,h*.22,'#58666b',INK,'stroke-width="2"')]
            for part in (.58,.65,.72):
                self.features.append(line(px+w*.34,py+h*part,px+w*.61,py+h*part,'#a3b0ac',1.5))
        self.labels.append(badge(px+w/2,py+15,ident,size=12,width=max(26,min(w-4,38))))

    def objective(self, objective):
        x,y=self.x(objective['x']),self.y(objective['y'])
        radius=objective.get('radius',3)
        self.overlay += [circle(x,y,radius*self.scale,'none',GOLD,
                                f'stroke-width="3" stroke-dasharray="8 5" data-objective="{objective["id"]}" data-control-radius="{radius}"'),
                         circle(x,y,6,'#f3cd58',INK,'stroke-width="2"'),
                         badge(x,y-radius*self.scale-12,objective['id'],color=GOLD,size=15)]

    def unit(self, x, y, label, side='blue', facing=None, ghost=False, radius=.75):
        px,py,r=self.x(x),self.y(y),radius*self.scale
        color=BLUE if side=='blue' else RED
        attrs=f'data-unit="{escape(label)}" data-center-x="{x}" data-center-y="{y}"'
        if ghost: attrs+=' opacity="0.48"'
        self.overlay.append(f'<g {attrs}>'
                            + circle(px+2,py+3,r,INK,extra='opacity=".25"')
                            + circle(px,py,r,PAPER if ghost else color,INK,'stroke-width="2.5"'))
        if not ghost:
            highlight = '#91bdd5' if side=='blue' else '#e7aa80'
            self.overlay.append(f'<path d="M{px-r*.65:g} {py-r*.45:g}Q{px:g} {py-r*1.1:g} {px+r*.65:g} {py-r*.45:g}" fill="none" stroke="{highlight}" stroke-width="2.5" stroke-linecap="round"/>')
        if facing is not None:
            self.overlay.append(f'<path d="M{px-5:g} {py-r+8:g}L{px:g} {py-r+2:g}L{px+5:g} {py-r+8:g}" fill="none" stroke="{color if ghost else "white"}" stroke-width="2" transform="rotate({facing} {px:g} {py:g})"/>')
        self.overlay += [text(px,py+5,label,13,'middle',color if ghost else 'white','bold'),'</g>']

    def arrow(self, start, end, kind='move'):
        color, marker = (BLUE,'move-arrow') if kind=='move' else (GOLD,'sight-arrow')
        extra=f'marker-end="url(#{marker})"'
        if kind!='move': extra+=' stroke-dasharray="8 5"'
        self.overlay.append(line(self.x(start[0]),self.y(start[1]),self.x(end[0]),self.y(end[1]),color,4,extra))

    def render(self, show_terrain_labels=True):
        out=[rect(self.left+4,self.top+5,self.width*self.scale,self.depth*self.scale,'#aaa98c'),
             rect(self.left,self.top,self.width*self.scale,self.depth*self.scale,'url(#ground)',INK,
                  f'data-board-width="{self.width}" data-board-depth="{self.depth}" data-scale="{self.scale}" stroke-width="3"')]+self.zones
        for value in range(0,int(self.width)+1,self.grid):
            out.append(line(self.x(value),self.top,self.x(value),self.y(0),GRID,1,'opacity=".5"'))
            if self.axes: out.append(text(self.x(value),self.y(0)+25,value,15,'middle',MUTED))
        for value in range(0,int(self.depth)+1,self.grid):
            out.append(line(self.left,self.y(value),self.x(self.width),self.y(value),GRID,1,'opacity=".5"'))
            if self.axes: out.append(text(self.left-14,self.y(value)+5,value,15,'end',MUTED))
        out.append(rect(self.left,self.top,self.width*self.scale,self.depth*self.scale,'none',INK,'stroke-width="3"'))
        return out+self.features+self.overlay+(self.labels if show_terrain_labels else [])


def terrain_key(x,y,kinds):
    out=[]
    tiles={'woods':(44,42),'rubble':(45,40),'blocking':(32,28),'fieldworks':(40,32),'water':(40,30)}
    for i,kind in enumerate(kinds):
        px=x+(i%4)*180;py=y+(i//4)*42
        tw,th=tiles[kind]
        out += [f'<svg x="{px:g}" y="{py:g}" width="32" height="25" viewBox="0 0 {tw} {th}" preserveAspectRatio="none" overflow="visible">'
                +(woods_shape(tw,th) if kind=='woods' else rect(0,0,tw,th,f'url(#{kind})',TERRAIN[kind][1],'stroke-width="2"'))+'</svg>',
                text(px+43,py+18,TERRAIN[kind][2],17)]
    return out
