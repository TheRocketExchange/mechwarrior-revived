"""Build measured scenario maps and teaching diagrams in one visual style."""
import copy
import json
from pathlib import Path
from map_style import Board, BLUE, RED, GOLD, INK, MUTED, TERRAIN, badge, circle, line, rect, save, terrain_key, text

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "diagrams"


def layouts():
    result = json.loads((ROOT / "layouts.json").read_text(encoding="utf-8"))
    starter = json.loads((ROOT / "first-contact.json").read_text(encoding="utf-8"))
    result['first-contact'] = {
        'title': 'First Contact', 'number': 'START', 'rounds': 4,
        'terrain': starter['terrain'],
        'objectives': [dict(starter['objective'], id='O1')],
        'deployment': [dict(id=side, name=side.upper(), low=limits[0], high=limits[1], side='blue' if side=='south' else 'red') for side,limits in starter['deployment'].items()],
        'note': 'One relay. Score at the end of rounds 2, 3, and 4.',
    }
    return result


def wider(layout):
    result = copy.deepcopy(layout)
    for item in result['terrain']+result['objectives']: item['x'] += 12
    for kind,prefix,y,depth in [('woods','W',18,8),('rubble','R',30,6)]:
        number = max([int(t['id'][1:]) for t in result['terrain'] if t['id'].startswith(prefix)],default=0)
        for i,(side,x) in enumerate([('West',3),('East',63)],1):
            result['terrain'].append(dict(id=f'{prefix}{number+i}', name=f'{side} outer {kind}', kind=kind, x=x, y=y, width=6, depth=depth))
    return result


def map_diagram(slug, data, wide=False):
    board_width=72 if wide else 48
    board=Board(board_width,48,84,154,672/board_width)
    for zone in data['deployment']: board.zone(zone)
    for feature in data['terrain']: board.terrain(feature)
    for objective in data['objectives']: board.objective(objective)
    body=board.render()
    if data.get('exit')=='north':
        body += [line(board.left,board.top,board.x(board.width),board.top,BLUE,6),
                 badge(board.x(board.width/2),board.top-15,'NORTH EDGE: EXIT',color=BLUE,size=15)]
    body += [text(790,143,'N',17,'middle',INK,'bold'),line(790,175,790,150,INK,2),
             '<path d="M785 156L790 147L795 156Z" fill="#243448"/>']
    y=board.y(0)+56
    body += [text(84,y,'Southwest corner = (0, 0)',17),text(756,y,'x → east   /   y ↑ north',17,'end')]
    body += terrain_key(62,y+26,[kind for kind in TERRAIN if any(t['kind']==kind for t in data['terrain'])])
    y+=84
    if data['objectives']:
        body += [circle(75,y-5,11,'none',GOLD,'stroke-dasharray="4 3" stroke-width="2"'),circle(75,y-5,3,GOLD,GOLD),text(96,y,'Objective point + 3-inch control ring',16)]
        y+=31
    keys=[(o['id'],f"{o['name']} ({o['x']}, {o['y']})") for o in data['objectives']]+[(t['id'],t['name']) for t in data['terrain']]
    for i,(ident,name) in enumerate(keys):
        xx=62+(i%2)*370; yy=y+(i//2)*24
        body += [text(xx,yy,ident,14,weight='bold'),text(xx+35,yy,name,14,fill=MUTED)]
    y+=((len(keys)+1)//2)*24+17
    body += [text(62,y,data['note'],16),text(62,y+26,'Terrain borders are exact. Patterns do not add obstacles.',15,fill=MUTED)]
    filename=slug+('-wide' if wide else '')+'-map.svg'
    save(OUT/filename,data['title'],f'{board_width} × 48 inches  /  6-inch grid  /  {data["rounds"]} rounds',body,840,y+90,
         f'{data["title"]} measured battlefield. North is up. Coordinates are inches from the southwest corner. '+data['note'],
         f'MISSION {data["number"]}  /  '+('LARGE & GRAND BATTLE' if wide else 'BATTLEFIELD LAYOUT'))


def movement():
    body=[]
    for i,(action,distance,note) in enumerate([('ADVANCE',4,'One ranged attack'),('MOVE',8,'No attack'),('RUSH',16,'No attack')]):
        top=170+i*185
        body += [text(42,top-22,action,20,fill=BLUE,weight='bold'),text(796,top-22,f'{distance} inches  /  {note}',18,'end')]
        board=Board(20,3,100,top,33,grid=2,axes=False)
        board.arrow((2.8,1.5),(2+distance-.8,1.5))
        board.unit(2,1.5,'M1',ghost=True,facing=90,radius=.6)
        board.unit(2+distance,1.5,'M1',facing=90,radius=.6)
        body+=board.render()
        for n in range(0,17,4): body.append(text(board.x(2+n),top+125,n,15,'middle',MUTED))
    body += [text(42,750,'M1 is the same model in each example. Pale marker = its starting position.',17),
             text(42,780,'Speed 8; no heat, equipment, or terrain modifiers. A shot still needs a legal target.',17),
             text(42,810,'Arrows show movement. Each small square is 2 inches across.',17,fill=MUTED)]
    save(OUT/'movement-and-fire.svg','Movement & shooting','Three orders at speed 8  /  Same distance scale in every lane',body,840,884,
         'Advance moves four inches and allows one ranged attack. Move travels eight inches without attacking. Rush travels sixteen without attacking. The same labeled base starts at zero in each lane.', 'EXAMPLE 01  /  MOVEMENT')


def objective_control():
    body=[]
    for left,enemy_x,label,note in [(50,9,'CONTROLLED','A scores 1'),(450,7,'CONTESTED','Neither side scores')]:
        board=Board(10,10,left,208,34,grid=2,axes=False)
        board.objective(dict(id='RELAY',x=5,y=5,radius=3))
        board.unit(4,5,'A',radius=.45)
        board.unit(enemy_x,5,'B',side='red',radius=.45)
        board.overlay += [line(board.x(5),board.y(5),board.x(5),board.y(8),GOLD,1),text(board.x(5)+9,board.y(6.4),'3″',17,fill=GOLD)]
        body += [text(left+170,166,label,23,'middle',BLUE if enemy_x==9 else RED,'bold')]+board.render()
        body.append(text(left+170,588,note,23,'middle',weight='bold'))
    body += [circle(62,642,10,BLUE,BLUE),text(82,648,'A: your base',19),circle(442,642,10,RED,RED),text(462,648,'B: enemy base',19),
             text(50,696,'Use base centers, not base edges. Both sides inside means contested.',18),
             text(50,726,'Only units eligible to control or contest are shown. Grid = 2 inches.',17,fill=MUTED)]
    save(OUT/'objective-control.svg','Who controls the relay?','Two views of the same 3-inch control area',body,840,800,
         'Left: A is inside the three-inch ring and B is outside, so A controls and scores. Right: both centers are inside, so the relay is contested. Base centers decide control.', 'EXAMPLE 02  /  OBJECTIVES')


def terrain_sight():
    board=Board(24,16,96,166,27,grid=2,axes=False)
    board.terrain(dict(id='W1',kind='woods',x=10,y=10,width=6,depth=4))
    board.terrain(dict(id='B1',kind='blocking',x=9,y=2,width=6,depth=4))
    board.arrow((3,12),(13,12),'sight');board.arrow((3,4),(21,4),'sight')
    for x,y,label,side,facing in [(3,12,'M1','blue',90),(13,12,'I1','red',None),(3,4,'M2','blue',90),(21,4,'M3','red',270)]:
        board.unit(x,y,label,side,facing,radius=.7)
    board.overlay += [badge(board.x(7),board.y(14.3),'CLEAR SIGHT',color=BLUE,size=15),
                      badge(board.x(18.8),board.y(14.3),'INFANTRY IN WOODS',color=RED,size=13),
                      badge(board.x(12),board.y(7.5),'BLOCKED',color=RED,size=16),
                      line(board.x(12)-8,board.y(4)-8,board.x(12)+8,board.y(4)+8,RED,4),line(board.x(12)-8,board.y(4)+8,board.x(12)+8,board.y(4)-8,RED,4)]
    body=board.render()+terrain_key(96,633,['woods','blocking'])
    body += [line(510,646,555,646,GOLD,3,'stroke-dasharray="8 5"'),text(568,652,'Sight line',17),
             text(96,704,'Top: woods do not block sight. I1 gets +3 ranged defense for being in woods.',17),
             text(96,736,'Bottom: the building blocks the line between the two base centers.',17),
             text(96,776,'Assume range and front arc are legal. M = ’Mech; I = infantry. Grid = 2 inches.',16,fill=MUTED)]
    save(OUT/'terrain-and-sight.svg','Terrain & line of sight','Check the line between base centers, then the target’s terrain',body,840,850,
         'The upper shot reaches infantry inside woods: sight is clear and infantry receives three ranged defense from cover. The lower shot crosses a blocking building and is illegal. Models have valid range and front arcs.', 'EXAMPLE 03  /  TERRAIN')


def terrain_movement():
    board=Board(20,8,90,178,33,grid=2,axes=False)
    board.terrain(dict(id='W1',kind='woods',x=7,y=2,width=4,depth=4))
    board.arrow((3,4),(15,4))
    board.unit(3,4,'M1',ghost=True,facing=90,radius=.6);board.unit(15,4,'M1',facing=90,radius=.6)
    for x,label in [(5,'4″ open'),(9,'4″ woods'),(13,'4″ open')]:
        board.overlay.append(badge(board.x(x),board.y(7),label,color=BLUE,size=16))
    body=board.render()+terrain_key(90,473,['woods'])
    body += [text(90,548,'12 inches traveled = 16 inches of movement',25,weight='bold'),text(90,588,'4 open + (4 woods × 2) + 4 open = 16',21,fill=BLUE),
             text(90,634,'A speed-8 ’Mech can cover this route with Rush; it cannot attack.',18),
             text(90,664,'No heat or equipment modifiers. Each grid square is 2 inches.',17,fill=MUTED)]
    save(OUT/'terrain-movement.svg','Moving through woods','Measure the route and pay for each terrain segment',body,840,738,
         'The model moves four inches through open ground, four through woods, then four through open ground. Twelve inches traveled costs sixteen movement because woods cost two per inch. A speed-eight Mech can Rush along the route.', 'EXAMPLE 04  /  MOVEMENT COST')


def readiness():
    body=[]
    steps=[('1 · FIRE','Ready','Committed','No pushing damage',''),('2 · FIRE','Committed','Spent','1 damage per surviving base','after its action'),('3 · MOVE / HOLD','Spent','Ready','Recover; no attack','')]
    for i,(action,before,after,note,detail) in enumerate(steps):
        x=24+i*272;cx=x+124
        body += [rect(x,154,248,266,'#e3ebf4','#a3b5cb'),rect(x,154,248,47,'#435f80'),text(cx,185,action,22,'middle','white','bold'),text(cx,245,before,23,'middle'),
                 line(cx,262,cx,299,BLUE,3,'marker-end="url(#move-arrow)"'),text(cx,337,after,25,'middle',RED if after=='Spent' else BLUE,'bold'),
                 text(cx,376,note,16,'middle'),text(cx,401,detail,16,'middle')]
    body += [text(28,467,'One vehicle or squad. Each step is a separate activation.',20),text(28,503,'Recover early from Committed to avoid pushing. ’Mechs use heat instead.',18)]
    save(OUT/'pushing-and-recovery.svg','Pushing & recovery','Readiness stays between rounds',body,840,580,
         'First Fire changes Ready to Committed. A second Fire changes Committed to Spent and each surviving base takes one pushing damage after acting. Move or Hold recovers to Ready. Recovering early avoids pushing.', 'EXAMPLE 05  /  READINESS')


def main():
    OUT.mkdir(exist_ok=True)
    for slug,data in layouts().items():
        map_diagram(slug,data)
        if slug!='first-contact': map_diagram(slug,wider(data),True)
    movement();objective_control();terrain_sight();terrain_movement();readiness()
    print('Generated 7 measured scenario maps and 5 teaching diagrams in the shared battlefield style.')


if __name__=='__main__': main()
