"""Touch events against real UI assets; native replies explicitly simulated."""
import json,threading,http.server
from pathlib import Path
from playwright.sync_api import sync_playwright
H=Path(__file__).resolve().parents[1];A=H/'android/assets/chat'
class Handler(http.server.SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(A),**kw)
 def log_message(self,*a):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
initial={'type':'state','model':'tools','profile':'normal','ready':True,'loading':False,'busy':False,'available':False,'thread':'old','history':[],'threads':[]}
checks=[]
def check(value,label):assert value,label;checks.append(label)
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage']);page=b.new_page(viewport={'width':393,'height':852},is_mobile=True,has_touch=True)
 page.add_init_script("window.calls=[];window.Android={dispatch:r=>{const x=JSON.parse(r);calls.push(x);if(x.type==='boot')setTimeout(()=>Liquid.receive("+json.dumps(initial)+"),0);}};")
 page.goto(f'http://127.0.0.1:{server.server_port}/');page.wait_for_function('window.Liquid');page.wait_for_timeout(250)
 page.tap('#model-button');check(page.locator('#overlay').is_visible(),'touch opens model picker');page.tap('[data-model="base"]');check(page.evaluate('calls.at(-1).type')=='selectModel','touch model choice reaches bridge');page.locator('#overlay').wait_for(state='hidden')
 page.tap('#menu');check(page.locator('#shade').is_visible(),'touch opens drawer');page.wait_for_timeout(300);page.tap('#new-chat');check(page.evaluate('calls.at(-1).type')=='newChat','drawer new chat reaches bridge')
 page.evaluate("Liquid.receive({type:'begin',text:'Etapa em andamento'})");page.tap('#new-top');check(page.evaluate('calls.at(-1).type')=='newChat','touch new chat not disabled during generation')
 page.evaluate("Liquid.receive({type:'switchPending',action:'newChat',message:'Interrompendo…'});Liquid.receive({type:'finish',text:'TEXTO ANTIGO',reason:'cancelled'})");check('TEXTO ANTIGO' not in page.locator('#timeline').inner_text(),'old finish cannot populate new pending chat')
 page.evaluate('(e)=>Liquid.receive(e)',dict(initial,thread='new'));page.tap('#message');page.locator('#message').fill('/help');page.tap('#send');check(page.locator('#sheet-title').inner_text()=='Comandos do chat','slash help works with touch');page.tap('#close-sheet');page.locator('#overlay').wait_for(state='hidden')
 check(page.locator('#send').evaluate('e=>getComputedStyle(e).webkitTapHighlightColor')=='rgba(0, 0, 0, 0)','touch uses no blue browser highlight');b.close()
server.shutdown();(H/'reports/touch_tests.json').write_text(json.dumps({'status':'passed','checks':len(checks),'details':checks,'scope':'Chromium mobile emulation with touch input, simulated Java bridge; not Android device execution'},indent=2)+'\n');print('TOUCH_CHECKS',len(checks))
