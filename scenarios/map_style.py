"""Shared SVG language for measured battlefields and worked examples.

Board coordinates are inches from the southwest corner. Terrain footprints
are exact; textures, labels and token symbols carry no additional rules.
"""
from html import escape

INK, MUTED = "#243448", "#52677e"
BLUE, RED, GOLD = "#245e94", "#a54a35", "#926818"
PAPER, GROUND, GRID = "#f4f7fa", "#ece9dc", "#c7cabb"
TERRAIN = {"woods": ("#d4dfbf", "#63794e", "Woods"),
           "rubble": ("#e3d7bd", "#8c7856", "Rubble"),
           "blocking": ("#b7bdc3", "#52606e", "Blocking"),
           "fieldworks": ("#ddcbaa", "#806044", "Fieldworks"),
           "water": ("#ccdde5", "#6a8b9d", "Shallow water")}


def text(x, y, value, size=18, anchor="start", fill=INK, weight="normal", extra=""):
    return f'<text x="{x:g}" y="{y:g}" font-size="{size}" text-anchor="{anchor}" fill="{fill}" font-weight="{weight}" {extra}>{escape(str(value))}</text>'


def rect(x, y, w, h, fill, stroke="none", extra=""):
    return f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="{fill}" stroke="{stroke}" {extra}/>'


def line(x1, y1, x2, y2, color=MUTED, width=2, extra=""):
    return f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" stroke="{color}" stroke-width="{width}" {extra}/>'


def circle(x, y, radius, fill="none", stroke=MUTED, extra=""):
    return f'<circle cx="{x:g}" cy="{y:g}" r="{radius:g}" fill="{fill}" stroke="{stroke}" {extra}/>'


def badge(x, y, value, fill=PAPER, color=INK, size=15, width=None):
    width = width or max(34, len(str(value)) * size * .61 + 14)
    return rect(x-width/2, y-size+1, width, size+9, fill, color, 'stroke-width="1"') + text(x, y+2, value, size, "middle", color, "bold")


DEFS = '''<defs>
<pattern id="woods" patternUnits="userSpaceOnUse" width="26" height="26"><rect width="26" height="26" fill="#d4dfbf"/><path d="M13 3L20 17H6Z M13 14V22" fill="#a9be8e" stroke="#788f60" stroke-width="1.2"/></pattern>
<pattern id="rubble" patternUnits="userSpaceOnUse" width="28" height="26"><rect width="28" height="26" fill="#e3d7bd"/><path d="M3 8L10 4L13 13L5 15Z M17 19L23 12L27 22Z" fill="#bdaf94" stroke="#918164"/><path d="M16 3L21 6M4 22L9 20" stroke="#9f8c6b"/></pattern>
<pattern id="blocking" patternUnits="userSpaceOnUse" width="24" height="24"><rect width="24" height="24" fill="#b7bdc3"/><path d="M0 24L24 0M-6 6L6 -6M18 30L30 18" stroke="#85919c" stroke-width="2"/></pattern>
<pattern id="fieldworks" patternUnits="userSpaceOnUse" width="28" height="24"><rect width="28" height="24" fill="#ddcbaa"/><path d="M0 7H9V17H19V7H28" fill="none" stroke="#806044" stroke-width="5"/><path d="M0 7H9V17H19V7H28" fill="none" stroke="#b79a70" stroke-width="2"/></pattern>
<pattern id="water" patternUnits="userSpaceOnUse" width="28" height="20"><rect width="28" height="20" fill="#ccdde5"/><path d="M0 10Q7 5 14 10T28 10" fill="none" stroke="#86a6b7"/></pattern>
<marker id="move-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0L10 5L0 10Z" fill="#245e94"/></marker>
<marker id="sight-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0L10 5L0 10Z" fill="#926818"/></marker>
</defs>'''


def save(path, title, subtitle, body, width, height, description, tag="FIELD GUIDE"):
    header = [rect(0, 0, width, height, PAPER), rect(0, 0, width, 82, "#344f70"),
              text(28, 25, tag, 12, fill="#c5d8ec", weight="bold", extra='letter-spacing="2"'),
              text(28, 60, title, 29, fill="white", weight="bold"),
              text(28, 111, subtitle, 18, fill=MUTED)]
    footer = [line(28, height-43, width-28, height-43, "#b4c3d4", 1),
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
        self.zones, self.features, self.overlay = [], [], []

    def x(self, value): return self.left + value*self.scale
    def y(self, value): return self.top + (self.depth-value)*self.scale

    def zone(self, zone):
        low, high = zone['low'], zone['high']
        blue = zone['side']=='blue'
        color = BLUE if blue else RED
        self.zones.append(rect(self.left, self.y(high), self.width*self.scale, (high-low)*self.scale,
                               '#d3e0eb' if blue else '#ead7cc', extra=f'data-zone="{zone["id"]}" data-low="{low}" data-high="{high}"'))
        for value in (low,high):
            if value not in (0,self.depth):
                self.zones.append(line(self.left,self.y(value),self.x(self.width),self.y(value),color,2,'stroke-dasharray="8 5"'))
        # Label only; the exact limits remain in the band and coordinate labels.
        label_y = self.y((low+high)/2)
        if high-low>8: label_y=self.y(high-1.8)
        self.overlay.append(badge(self.x(self.width/2), label_y+3, f'{zone["name"]}  ·  y {low}–{high}', '#f4f7fa',color,15))

    def terrain(self, feature):
        kind, ident = feature['kind'], feature['id']
        px, py = self.x(feature['x']), self.y(feature['y']+feature['depth'])
        w,h = feature['width']*self.scale, feature['depth']*self.scale
        self.features.append(rect(px,py,w,h,f'url(#{kind})',TERRAIN[kind][1],
                                  f'stroke-width="2" data-terrain="{ident}" data-kind="{kind}"'))
        if kind=='blocking' and min(w,h)>24:
            self.features += [rect(px+6,py+6,w-12,h-12,'#a4adb5','#677685'),
                              line(px+6,py+6,px+w-6,py+h-6,'#87949f',1),
                              line(px+6,py+h-6,px+w-6,py+6,'#87949f',1)]
        self.features.append(badge(px+w/2,py+15,ident,size=12,width=max(26,min(w-4,38))))

    def objective(self, objective):
        x,y=self.x(objective['x']),self.y(objective['y'])
        radius=objective.get('radius',3)
        self.overlay += [circle(x,y,radius*self.scale,'none',GOLD,
                                f'stroke-width="2.5" stroke-dasharray="6 4" data-objective="{objective["id"]}" data-control-radius="{radius}"'),
                         circle(x,y,5,GOLD,'white','stroke-width="1.5"'),
                         badge(x,y-radius*self.scale-12,objective['id'],color=GOLD,size=15)]

    def unit(self, x, y, label, side='blue', facing=None, ghost=False, radius=.75):
        px,py,r=self.x(x),self.y(y),radius*self.scale
        color=BLUE if side=='blue' else RED
        attrs=f'data-unit="{escape(label)}" data-center-x="{x}" data-center-y="{y}"'
        if ghost: attrs+=' opacity="0.48"'
        self.overlay.append(f'<g {attrs}>'+circle(px,py,r,PAPER if ghost else color,color,'stroke-width="2"'))
        if facing is not None:
            self.overlay.append(f'<path d="M{px-5:g} {py-r+8:g}L{px:g} {py-r+2:g}L{px+5:g} {py-r+8:g}" fill="none" stroke="{color if ghost else "white"}" stroke-width="2" transform="rotate({facing} {px:g} {py:g})"/>')
        self.overlay += [text(px,py+5,label,13,'middle',color if ghost else 'white','bold'),'</g>']

    def arrow(self, start, end, kind='move'):
        color, marker = (BLUE,'move-arrow') if kind=='move' else (GOLD,'sight-arrow')
        extra=f'marker-end="url(#{marker})"'
        if kind!='move': extra+=' stroke-dasharray="8 5"'
        self.overlay.append(line(self.x(start[0]),self.y(start[1]),self.x(end[0]),self.y(end[1]),color,3,extra))

    def render(self):
        out=[rect(self.left,self.top,self.width*self.scale,self.depth*self.scale,GROUND,INK,
                  f'data-board-width="{self.width}" data-board-depth="{self.depth}" data-scale="{self.scale}" stroke-width="2"')]+self.zones
        for value in range(0,int(self.width)+1,self.grid):
            out.append(line(self.x(value),self.top,self.x(value),self.y(0),GRID,1))
            if self.axes: out.append(text(self.x(value),self.y(0)+25,value,15,'middle',MUTED))
        for value in range(0,int(self.depth)+1,self.grid):
            out.append(line(self.left,self.y(value),self.x(self.width),self.y(value),GRID,1))
            if self.axes: out.append(text(self.left-14,self.y(value)+5,value,15,'end',MUTED))
        return out+self.features+self.overlay


def terrain_key(x,y,kinds):
    out=[]
    for i,kind in enumerate(kinds):
        px=x+(i%4)*180;py=y+(i//4)*42
        out += [rect(px,py,32,25,f'url(#{kind})',TERRAIN[kind][1]),text(px+43,py+18,TERRAIN[kind][2],17)]
    return out
