"""Exercise the offline site in an isolated Chrome on local debugging port 9234.

Optional QA dependency: websocket-client. Install in web/.qa/python or the environment.
This script only navigates local packet files and saves screenshots under web/.qa.
"""
import base64
import argparse
import json
import sys
import time
from pathlib import Path
from urllib.parse import quote
from urllib.request import build_opener, ProxyHandler

ROOT = Path(__file__).resolve().parent.parent
QA = ROOT / "web/.qa"
sys.path.insert(0,str(QA / "python"))
import websocket
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--port", type=int, default=9234)
args = parser.parse_args()

opener=build_opener(ProxyHandler({}))
targets=json.loads(opener.open(f'http://127.0.0.1:{args.port}/json',timeout=10).read())
target=next(t for t in targets if t['type']=='page')
ws=websocket.create_connection(target['webSocketDebuggerUrl'],suppress_origin=True,timeout=20)
counter=0
exceptions=[]


def call(method,params=None):
    global counter
    counter+=1
    ws.send(json.dumps({'id':counter,'method':method,'params':params or {}}))
    while True:
        response=json.loads(ws.recv())
        if response.get('method')=='Runtime.exceptionThrown':
            exceptions.append(response['params'])
        if response.get('id')==counter:
            assert 'error' not in response,response
            return response.get('result',{})


def js(code):
    response=call('Runtime.evaluate',{'expression':code,'returnByValue':True,'awaitPromise':True,'userGesture':True})
    assert 'exceptionDetails' not in response,response
    return response.get('result',{}).get('value')


def wait(condition):
    deadline=time.time()+20
    while time.time()<deadline:
        if js(condition): return
        time.sleep(0.1)
    raise AssertionError(condition)


def open_page(name,condition):
    url=(ROOT/'site'/name.split('?')[0]).as_uri()+('?' + name.split('?',1)[1] if '?' in name else '')
    call('Page.navigate',{'url':url})
    wait("location.href==="+json.dumps(url)+" && document.readyState==='complete' && ("+condition+")")


def screenshot(name):
    image=call('Page.captureScreenshot',{'format':'png','captureBeyondViewport':False})
    (QA/(name+'.png')).write_bytes(base64.b64decode(image['data']))


def input_value(selector,value):
    js(f"document.querySelector({json.dumps(selector)}).value={json.dumps(value)};document.querySelector({json.dumps(selector)}).dispatchEvent(new Event('input',{{bubbles:true}}))")


call('Page.enable')
call('Runtime.enable')
call('Emulation.setDeviceMetricsOverride',{'width':1440,'height':1100,'deviceScaleFactor':1,'mobile':False})
open_page('units.html',"document.querySelectorAll('.unit-tile').length===24")
assert js("document.querySelector('#unit-count').textContent.includes('1,649')")
wait("[...document.querySelectorAll('.unit-photo img')].filter(i=>i.getBoundingClientRect().top<1100).every(i=>i.complete&&i.naturalWidth>0)")
screenshot('catalog-desktop')
js("document.querySelector('#unit-grid').scrollIntoView()")
wait("[...document.querySelectorAll('.unit-photo img')].filter(i=>i.getBoundingClientRect().top<1100).every(i=>i.complete&&i.naturalWidth>0)")
screenshot('catalog-cards')
js("document.querySelector('#unit-next').click()")
assert js("document.querySelector('#unit-page').textContent.startsWith('Page 2 ')")
input_value('#unit-query','AOD108')
assert js("document.querySelectorAll('.unit-tile').length===1 && document.querySelector('.unit-tile').href.endsWith('id=AOD108')")
input_value('#unit-query','no-such-miniature-xxxx')
assert js("Boolean(document.querySelector('.empty-catalog'))")
js("document.querySelector('#unit-filters').reset()")
wait("document.querySelectorAll('.unit-tile').length===24")
input_value('#unit-category','Mech')
input_value('#unit-status','core')
assert js("[...document.querySelectorAll('.unit-tile')].every(a=>{const u=MW_CATALOG.units.find(u=>a.href.endsWith('id='+u.id));return u.category==='Mech'&&u.core_legal})")
input_value('#unit-sort','points')
assert js("(()=>{const p=[...document.querySelectorAll('.unit-points')].map(p=>parseInt(p.textContent));return p.every((n,i)=>!i||n>=p[i-1])})()")
open_page('unit.html?id=AOD108',"Boolean(document.querySelector('#dial-forward'))")
assert js("document.querySelector('h1').textContent==='Dasher II'")
assert js("document.querySelector('.unit-assignment').textContent.includes('Roster ID') && document.querySelector('.unit-assignment').textContent.includes('Pilot:')")
assert js("document.querySelector('.full-track').tagName==='SECTION' && getComputedStyle(document.querySelector('.full-track')).display!=='none'")
assert js("document.querySelectorAll('.full-track [data-click]').length===14")
assert js("document.querySelector('.full-track').textContent.includes('End') && document.querySelector('.dial-note').textContent.includes('starting total')")
assert js("document.querySelector('.profile-points').textContent.startsWith(String(window.MW_CATALOG.units.find(u=>u.id==='AOD108').cost.points))")
wait("document.querySelector('.profile-photo img').complete")
screenshot('unit-desktop')
printout=call('Page.printToPDF',{'printBackground':True,'paperWidth':8.5,'paperHeight':11,'preferCSSPageSize':True})
(QA/'unit-browser-print.pdf').write_bytes(base64.b64decode(printout['data']))
from pypdf import PdfReader
printed_text='\n'.join(page.extract_text() for page in PdfReader(QA/'unit-browser-print.pdf').pages)
assert all(value in printed_text for value in ('Full combat dial','Heat dial','Secondary damage','Stop','End','SD'))
js("document.querySelector('#dial-forward').click()")
assert js("document.querySelector('.dial-controls h2').textContent.includes('click 2')")
js("document.querySelector('#dial-reset').click()")
assert js("document.querySelector('.dial-controls h2').textContent.includes('Starting dial')")
js("document.querySelector('#rocket-choice').value='secondary';document.querySelector('#rocket-choice').dispatchEvent(new Event('change'))")
assert js("parseInt(document.querySelector('.profile-points').textContent)===MW_CATALOG.units.find(u=>u.id==='AOD108').rocket_options.secondary.points")
assert js("document.querySelector('.weapon-table').textContent.includes('Rocket')")
open_page('unit.html?id=AOD050',"Boolean(document.querySelector('#dial-forward'))")
assert js("document.querySelector('.unit-assignment').textContent.includes('Carrier: Yes / No') && document.querySelector('.unit-assignment').textContent.includes('Assigned squad:')")
assert js("document.querySelector('.unit-assignment').textContent.includes('Ready / Committed / Spent')")
js("document.querySelector('.cost-details').open=true")
assert js("document.querySelector('.cost-details').textContent.includes(MW_CATALOG.units.find(u=>u.id==='AOD050').cost.breakdown.readiness_factor.toFixed(3))")
screenshot('readiness-cost')
open_page('readiness.html',"document.querySelector('h1').textContent==='Readiness reference'")
assert js("document.querySelector('article').textContent.includes('Keep readiness between rounds')")
screenshot('readiness-desktop')
open_page('combat-rhythm.html',"document.querySelector('h1').textContent==='How v0.3 changes a battle'")
assert js("document.querySelector('article').textContent.includes('readiness only')")
js("document.querySelector('[data-search-open]').click()")
input_value('#rule-search','AOD030')
assert js("document.querySelector('.search-result').href.endsWith('id=AOD030')")
js("document.querySelector('.close-search').click()")
call('Emulation.setDeviceMetricsOverride',{'width':390,'height':844,'deviceScaleFactor':1,'mobile':True})
open_page('unit.html?id=AOD108',"Boolean(document.querySelector('#dial-forward'))")
wait("document.querySelector('.profile-photo img').complete")
assert js("document.documentElement.scrollWidth <= innerWidth"),'Unit mobile overflow'
screenshot('unit-mobile')
open_page('unit.html?id=D006',"Boolean(document.querySelector('#dial-forward'))")
assert js("document.querySelector('.unit-assignment').textContent.includes('Squad:') && document.querySelector('.unit-assignment').textContent.includes('Assigned carrier:')")
assert js("document.documentElement.scrollWidth <= innerWidth"),'Infantry mobile overflow'
open_page('unit.html?id=BF019',"document.querySelector('h1').textContent.includes('Ares')")
assert js("document.querySelectorAll('.full-track [data-click]').length===23 && document.querySelectorAll('.screen-dials table').length===3")
assert js("document.documentElement.scrollWidth <= innerWidth"),'Long-dial mobile overflow'
printout=call('Page.printToPDF',{'printBackground':True,'paperWidth':8.5,'paperHeight':11,'preferCSSPageSize':True})
(QA/'long-dial-browser-print.pdf').write_bytes(base64.b64decode(printout['data']))
printed_text='\n'.join(page.extract_text() for page in PdfReader(QA/'long-dial-browser-print.pdf').pages)
assert all(value in printed_text for value in ('Full combat dial','Heat dial','23','SD','End'))
open_page('units.html',"document.querySelectorAll('.unit-tile').length===24")
assert js("document.documentElement.scrollWidth <= innerWidth"),'Catalog mobile overflow'
screenshot('catalog-mobile')
open_page('rules.html',"Boolean(document.getElementById('7-combat'))")
assert js("document.documentElement.scrollWidth <= innerWidth"),'Rules mobile overflow'
screenshot('rules-mobile')
open_page('readiness.html',"document.querySelector('h1').textContent==='Readiness reference'")
assert js("document.documentElement.scrollWidth <= innerWidth"),'Readiness mobile overflow'
screenshot('readiness-mobile')
open_page('unit.html?id=P001',"Boolean(document.querySelector('#dial-forward'))")
assert js("Boolean(document.querySelector('.catalog-restriction'))")
js("document.querySelector('[data-click=\"14\"]').click()")
assert js("document.querySelector('.dial-controls h2').textContent.includes('click 15')")
open_page('unit.html?id=NOT-A-UNIT',"document.querySelector('#unit-detail').textContent.includes('Unit not found')")
call('Emulation.setDeviceMetricsOverride',{'width':1440,'height':1100,'deviceScaleFactor':1,'mobile':False})
open_page('builder.html',"Boolean(document.querySelector('#force-name'))")
js("localStorage.removeItem('mw-revived-force-v1')")
open_page('builder.html?test=empty',"document.querySelectorAll('[data-roster-group]').length===0")
for unit_id in ('AOD108','AOD112','AOD096','AOD104','D006','AOD050'):
    input_value('#force-query',unit_id)
    js(f"document.querySelector('[data-add=\"{unit_id}\"]').click()")
input_value('#force-query','D009')
js("document.querySelector('[data-destination=\"D009\"]').value='C1';document.querySelector('[data-add=\"D009\"]').click()")
js("document.querySelector('[data-group=\"V1\"][data-field=\"carrier\"]').click()")
js("const field=document.querySelector('[data-group=\"V1\"][data-field=\"passengers\"]');field.value='C1';field.dispatchEvent(new Event('change',{bubbles:true}))")
js("const rocket=document.querySelector('[data-group=\"M1\"][data-field=\"rocket_slot\"]');rocket.value='secondary';rocket.dispatchEvent(new Event('change',{bubbles:true}))")
input_value('#force-name','Desert Watch')
assert js("document.querySelector('#force-check-title').textContent==='All standard force limits met'")
assert js("document.querySelectorAll('[data-roster-group]').length===6")
saved=js("JSON.parse(localStorage.getItem('mw-revived-force-v1'))")
assert saved['groups'][0]['rocket_slot']=='secondary'
assert saved['groups'][-1]['passengers']=='C1'
open_page('builder.html',"document.querySelector('#force-name').value==='Desert Watch'")
assert js("document.querySelectorAll('[data-roster-group]').length===6")
screenshot('builder-desktop')
call('Emulation.setDeviceMetricsOverride',{'width':390,'height':844,'deviceScaleFactor':1,'mobile':True})
assert js("document.documentElement.scrollWidth <= innerWidth"),'Builder mobile overflow'
screenshot('builder-mobile')
call('Emulation.setDeviceMetricsOverride',{'width':1440,'height':1100,'deviceScaleFactor':1,'mobile':False})
downloads=QA/'full-dial'
downloads.mkdir(exist_ok=True)
call('Browser.setDownloadBehavior',{'behavior':'allow','downloadPath':str(downloads.resolve())})
export_path=downloads/'Desert-Watch.json'
export_path.unlink(missing_ok=True)
js("document.querySelector('#force-export').click()")
deadline=time.time()+10
while not export_path.exists() and time.time()<deadline: time.sleep(.1)
assert json.loads(export_path.read_text(encoding='utf-8'))==saved
js("window.confirm=()=>true;document.querySelector('#force-new').click()")
assert js("document.querySelectorAll('[data-roster-group]').length===0")
root=call('DOM.getDocument')['root']['nodeId']
input_id=call('DOM.querySelector',{'nodeId':root,'selector':'#force-import'})['nodeId']
call('DOM.setFileInputFiles',{'nodeId':input_id,'files':[str(export_path.resolve())]})
wait("document.querySelector('#force-name').value==='Desert Watch'")
assert js("JSON.parse(localStorage.getItem('mw-revived-force-v1'))")==saved
broken=downloads/'invalid-force.json'
broken.write_text('{"groups":[{"id":"M1","members":["UNKNOWN"]}]}',encoding='utf-8')
call('DOM.setFileInputFiles',{'nodeId':input_id,'files':[str(broken.resolve())]})
wait("document.querySelector('#force-message').textContent.includes('Could not import')")
assert js("JSON.parse(localStorage.getItem('mw-revived-force-v1'))")==saved
existing_targets={target['id'] for target in json.loads(opener.open(f'http://127.0.0.1:{args.port}/json').read())}
js("document.querySelector('#force-cards').click()")
deadline=time.time()+10
while time.time()<deadline:
    targets=json.loads(opener.open(f'http://127.0.0.1:{args.port}/json').read())
    target=next((t for t in targets if t['id'] not in existing_targets and t.get('type')=='page' and 'force-cards.html#list=' in t.get('url','')),None)
    if target: break
    time.sleep(.1)
assert target,'No selected-card tab opened'
ws.close()
ws=websocket.create_connection(target['webSocketDebuggerUrl'],suppress_origin=True,timeout=20)
call('Page.enable');call('Runtime.enable')
call('Emulation.setDeviceMetricsOverride',{'width':1100,'height':1100,'deviceScaleFactor':1,'mobile':False})
wait("document.querySelectorAll('.print-unit-card').length===8")
wait("[...document.querySelectorAll('.print-unit-card img')].every(img=>img.complete&&img.naturalWidth>0)")
assert js("[...document.querySelectorAll('[data-card-id]')].map(card=>card.dataset.cardId)")==['M1','M2','M3','M4','C1a','C1b','C1c','V1']
assert js("document.querySelector('[data-card-id=\"M1\"]').textContent.includes('Secondary: Rocket')")
assert js("document.querySelector('[data-card-id=\"C1a\"]').textContent.includes('Assigned carrier: V1')")
screenshot('selected-cards')
printout=call('Page.printToPDF',{'printBackground':True,'preferCSSPageSize':True,'paperWidth':8.5,'paperHeight':11})
selected_pdf=QA/'selected-unit-cards.pdf'
selected_pdf.write_bytes(base64.b64decode(printout['data']))
selected_reader=PdfReader(selected_pdf)
assert len(selected_reader.pages)==4,len(selected_reader.pages)
selected_text='\n'.join(page.extract_text() for page in selected_reader.pages)
assert selected_text.count('Catalog ID:')==8
assert all(label in selected_text for label in ('C1a','C1b','C1c','V1','Gunner','Rocket','HEAT DIAL','COMBAT DIAL','SD'))
long_force={'name':'Long card layout','groups':[{'id':'M1','members':['BF019'],'pilot':'Gunner'},{'id':'A1','members':['CA129']}]}
call('Page.navigate',{'url':(ROOT/'site/force-cards.html').as_uri()+'#list='+quote(json.dumps(long_force))})
wait("document.querySelector('[data-catalog-id=\"BF019\"]') && document.querySelectorAll('.print-unit-card').length===2")
wait("[...document.querySelectorAll('.print-unit-card img')].every(img=>img.complete&&img.naturalWidth>0)")
assert js("document.querySelector('#force-card-status').textContent.includes('Draft list')")
assert js("[...document.querySelectorAll('.print-unit-card')].every(card=>card.scrollHeight<=card.clientHeight+1)"),'Selected card content clipped'
printout=call('Page.printToPDF',{'printBackground':True,'preferCSSPageSize':True,'paperWidth':8.5,'paperHeight':11})
(QA/'selected-long-unit-cards.pdf').write_bytes(base64.b64decode(printout['data']))
assert len(PdfReader(QA/'selected-long-unit-cards.pdf').pages)==1
assert not exceptions,exceptions
ws.close()
print('Browser checks passed: catalog, dials, printing, mobile layouts, force building, assignments, saving, JSON export/import, invalid imports, and selected-card PDFs. No JavaScript exceptions.')
