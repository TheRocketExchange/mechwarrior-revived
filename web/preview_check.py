"""Exercise the offline site in an isolated Chrome on local debugging port 9234.

Optional QA dependency: websocket-client. Install in web/.qa/python or the environment.
This script only navigates local packet files and saves screenshots under web/.qa.
"""
import base64
import json
import sys
import time
from pathlib import Path
from urllib.request import build_opener, ProxyHandler

ROOT = Path(__file__).resolve().parent.parent
QA = ROOT / "web/.qa"
sys.path.insert(0,str(QA / "python"))
import websocket

opener=build_opener(ProxyHandler({}))
targets=json.loads(opener.open('http://127.0.0.1:9234/json').read())
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
    response=call('Runtime.evaluate',{'expression':code,'returnByValue':True,'awaitPromise':True})
    assert 'exceptionDetails' not in response,response
    return response.get('result',{}).get('value')


def wait(condition):
    deadline=time.time()+20
    while time.time()<deadline:
        if js(condition): return
        time.sleep(0.1)
    raise AssertionError(condition)


def open_page(name,condition):
    call('Page.navigate',{'url':(ROOT/'site'/name.split('?')[0]).as_uri()+('?' + name.split('?',1)[1] if '?' in name else '')})
    wait("document.readyState==='complete' && ("+condition+")")


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
assert js("document.querySelector('.profile-points').textContent.startsWith(String(window.MW_CATALOG.units.find(u=>u.id==='AOD108').cost.points))")
wait("document.querySelector('.profile-photo img').complete")
screenshot('unit-desktop')
printout=call('Page.printToPDF',{'printBackground':True,'paperWidth':8.5,'paperHeight':11,'preferCSSPageSize':True})
(QA/'unit-browser-print.pdf').write_bytes(base64.b64decode(printout['data']))
js("document.querySelector('#dial-forward').click()")
assert js("document.querySelector('.dial-controls h2').textContent.includes('click 2')")
js("document.querySelector('#dial-reset').click()")
assert js("document.querySelector('.dial-controls h2').textContent.includes('Starting dial')")
js("document.querySelector('#rocket-choice').value='secondary';document.querySelector('#rocket-choice').dispatchEvent(new Event('change'))")
assert js("parseInt(document.querySelector('.profile-points').textContent)===MW_CATALOG.units.find(u=>u.id==='AOD108').rocket_options.secondary.points")
assert js("document.querySelector('.weapon-table').textContent.includes('Rocket')")
open_page('unit.html?id=AOD050',"Boolean(document.querySelector('#dial-forward'))")
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
assert not exceptions,exceptions
ws.close()
print('Browser checks passed: photos, pagination, search, filters, sorting, dials, Rocket pricing, missing IDs, and mobile overflow. No JavaScript exceptions.')
