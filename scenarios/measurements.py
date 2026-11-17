"""Dimension lines for scenario maps, in battlefield inches."""


def placement_dimensions(terrain, objectives, width, depth=48, zones=()):
    """Route edge-to-feature measurements through open space where possible.

    Each endpoint measures a terrain edge or objective center. A short witness
    line joins any displaced dimension line to that exact endpoint.
    """
    rectangles = [(t['x'], t['y'], t['x']+t['width'], t['y']+t['depth']) for t in terrain]
    result, labels = [], []
    for obj in objectives:
        labels.append((obj['x']-1.7,obj['y']+3.2,obj['x']+1.7,obj['y']+5.3))
    for zone in zones:
        cy = (zone['low']+zone['high'])/2
        if zone['high']-zone['low']>8: cy=zone['high']-1.8
        cy=zone.get('label_y',cy)
        labels.append((width/2-4,cy-1,width/2+4,cy+1))

    def overlap(a, b):
        return max(0, min(a[2], b[2])-max(a[0], b[0])) * max(0, min(a[3], b[3])-max(a[1], b[1]))

    for feature in terrain + objectives:
        ident = feature['id']
        x, y = feature['x'], feature['y']
        w, h = feature.get('width', 0), feature.get('depth', 0)
        for axis in ('x', 'y'):
            start, span, limit = (x, w, width) if axis=='x' else (y, h, depth)
            cross, cross_span = (y, h) if axis=='x' else (x, w)
            edge = 0 if start+span/2 <= limit/2 else limit
            end = start if edge==0 else start+span
            distance = abs(end-edge)
            center = cross+cross_span/2
            lanes = [center] + [v for gap in (1.5, 3, 5, 8, 11) for v in (cross-gap, cross+cross_span+gap)]
            candidates = []
            for lane in lanes:
                if not 1 <= lane <= (depth if axis=='x' else width)-1: continue
                low, high = sorted((edge, end))
                corridor = (low, lane-.35, high, lane+.35) if axis=='x' else (lane-.35, low, lane+.35, high)
                witness = min(max(lane, cross), cross+cross_span)
                for fraction in (.5, .3, .7, .2, .8):
                    along = edge+(end-edge)*fraction
                    lx, ly = (along, lane) if axis=='x' else (lane, along)
                    label_box = (lx-1.25, ly-.65, lx+1.25, ly+.65)
                    score = abs(lane-center)*2 + abs(fraction-.5)
                    score += sum(overlap(corridor, r)*45 + overlap(label_box, r)*100 for r in rectangles)
                    score += sum(overlap(label_box, r)*300 + overlap(corridor, r)*150 for r in labels)
                    for prior in result:
                        p_low, p_high = sorted((prior['edge'], prior['end']))
                        p_lane=prior['lane']
                        p_corridor=(p_low,p_lane-.35,p_high,p_lane+.35) if prior['axis']=='x' else (p_lane-.35,p_low,p_lane+.35,p_high)
                        score += overlap(label_box,p_corridor)*150
                        if prior['axis']==axis and abs(prior['lane']-lane)<1:
                            score += max(0,min(high,p_high)-max(low,p_low))*70
                        elif prior['axis']!=axis and low<prior['lane']<high and p_low<lane<p_high:
                            score += 3
                    candidates.append((score, lane, witness, lx, ly, label_box))
            _, lane, witness, lx, ly, label_box = min(candidates)
            result.append(dict(id=ident, axis=axis, edge=edge, end=end, lane=lane,
                               witness=witness, distance=distance, label=(lx,ly)))
            labels.append(label_box)
    return result
