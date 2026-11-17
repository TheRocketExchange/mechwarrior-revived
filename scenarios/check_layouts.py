"""Audit terrain spacing, routes and direct firing lanes (not game balance).

Uses a 3-inch round base as a movement probe and centers on a 2-inch grid.
Line-of-sight samples ignore units, facing, cover bonuses and equipment.
The percentage is clear center-to-center lines, not a hit or win probability.
"""
import argparse
import json
import math
from collections import deque
from itertools import combinations
from pathlib import Path

from generate_diagrams import layouts, wider


def bounds(t):
    return t['x'],t['y'],t['x']+t['width'],t['y']+t['depth']


def gap(a,b):
    ax,ay,ar,at=bounds(a);bx,by,br,bt=bounds(b)
    return math.hypot(max(ax-br,bx-ar,0),max(ay-bt,by-at,0))


def blocked(a,b,t):
    """Closed segment intersects a closed rectangle; grazing blocks sight."""
    lo,hi=0.,1.
    rect=bounds(t)
    for axis in (0,1):
        delta=b[axis]-a[axis]
        if abs(delta)<1e-9:
            if not rect[axis]<=a[axis]<=rect[axis+2]:return False
        else:
            near,far=sorted(((rect[axis]-a[axis])/delta,(rect[axis+2]-a[axis])/delta))
            lo,hi=max(lo,near),min(hi,far)
            if lo>hi:return False
    return True


def legal(point,terrain,radius=1.5):
    for t in terrain:
        if t['kind'] not in ('blocking','fieldworks'):continue
        x,y,r,top=bounds(t)
        distance=math.hypot(point[0]-max(x,min(point[0],r)),point[1]-max(y,min(point[1],top)))
        if distance<radius-1e-9:return False
    return True


def audit(data,validate=True):
    width=data.get('width',48);terrain=data['terrain'];solid=[t for t in terrain if t['kind']=='blocking']
    zones=data['deployment'];objectives=data['objectives']
    if validate:
        assert len({t['id'] for t in terrain})==len(terrain)
        for t in terrain:
            x,y,r,top=bounds(t)
            assert 0<=x<r<=width and 0<=y<top<=48,t['id']
        for a,b in combinations(terrain,2):
            assert gap(a,b)>=4-1e-9,(a['id'],b['id'],'less than 4 inches between terrain footprints')
        for o in objectives:
            assert legal((o['x'],o['y']),solid,0.01),o['id']

    grid=[(x,y) for x in range(2,width,2) for y in range(2,48,2) if legal((x,y),terrain)]
    def zone_points(zone):return [p for p in grid if zone['low']+1.5<=p[1]<=zone['high']-1.5]
    south=zone_points(zones[0]);north=zone_points(zones[1])
    # Southern approach band, excluding the opposing deployment.
    approaches=[p for p in grid if zones[0]['high']<p[1]<=min(zones[0]['high']+16,zones[1]['low'])]
    sight={}
    for distance in (24,36):
        pairs=[(a,b) for a in north for b in approaches if math.dist(a,b)<=distance]
        clear=sum(not any(blocked(a,b,t) for t in solid) for a,b in pairs)
        sight[f'clear_{distance}']=round(100*clear/max(1,len(pairs)),1)
    if validate:
        assert sight['clear_24']<=60,'Too many clear firing lines into the approach'
        if zones[0]['id']=='south':
            for t in solid:
                assert any(other['x']==width-t['x']-t['width'] and other['y']==48-t['y']-t['depth']
                    and other['width']==t['width'] and other['depth']==t['depth'] for other in solid),'Unequal blocking terrain for opposing edges'

    # Routes use a finer grid and expanded rectangles so every swept base fits.
    # This is conservative at corners; soft cover is traversable but not free.
    hard=[t for t in terrain if t['kind'] in ('blocking','fieldworks')]
    expanded=[dict(t,x=t['x']-1.5,y=t['y']-1.5,width=t['width']+3,depth=t['depth']+3) for t in hard]
    cells={(x,y) for x in range(2,width-1) for y in range(2,47) if legal((x,y),terrain)}
    def reach(starts):
        seen=set(starts)&cells;queue=deque(seen)
        while queue:
            p=queue.popleft()
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                q=(p[0]+dx,p[1]+dy)
                if q in cells and q not in seen and not any(blocked(p,q,t) for t in expanded):
                    seen.add(q);queue.append(q)
        return seen
    reached=reach(south)
    if validate:
        assert any(p[1]==46 for p in reached),'No traversable route to north edge'
        for zone in zones:
            connected=reach(zone_points(zone))
            for o in objectives:
                assert any(math.dist(p,(o['x'],o['y']))<=3 for p in connected),(zone['id'],o['id'],'objective unreachable')
        assert len({x for x,y in reached if y==46})>=width//2,'Exit routes too narrow'
    cover=sum(t['width']*t['depth'] for t in terrain)/(width*48)
    return dict(features=len(terrain),blocking=len(solid),terrain_percent=round(100*cover,1),
                min_gap=round(min(gap(a,b) for a,b in combinations(terrain,2)),1),
                **sight)


def all_layouts():
    result={}
    for name,data in layouts().items():
        result[name]=dict(data,width=48)
        if name!='first-contact':result[name+'-wide']=dict(wider(data),width=72)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before',type=Path)
    args=parser.parse_args()
    previous=json.loads(args.before.read_text(encoding='utf-8')) if args.before else {}
    for name,data in all_layouts().items():
        metrics=audit(data)
        if name in previous:metrics={'before':audit(previous[name],False),'after':metrics}
        print(name+': '+json.dumps(metrics))


if __name__=='__main__':main()
