"""Actual bundled UI in Chromium with a mocked Java bridge; never phone/inference QA."""
import contextlib,http.server,json,threading,time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];H=ROOT/'android_ui031';ASSETS=H/'android/assets/chat';SHOTS=Path('/dev/shm/liquid-ui031-shots');SHOTS.mkdir(exist_ok=True)
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw):super().__init__(*a,directory=str(ASSETS),**kw)
    def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
checks=[]
def check(condition,label):
    assert condition,label;checks.append(label)
initial={'type':'state','model':'tools','profile':'normal','ready':True,'loading':False,'busy':False,'available':False,'thread':'test','history':[],'threads':[{'id':'example','title':'Uma função para organizar ideias','model':'tools'}]}
mock="""window.calls=[];window.Android={dispatch(raw){const c=JSON.parse(raw);window.calls.push(c);if(c.type==='boot')setTimeout(()=>Liquid.receive(INITIAL),0);if(c.type==='setProfile')Liquid.receive({type:'profile',id:c.id});}};""".replace('INITIAL',json.dumps(initial))
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
    page=browser.new_page(viewport={'width':393,'height':852},device_scale_factor=1)
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.add_init_script(mock);page.goto(f'http://127.0.0.1:{server.server_port}/');page.wait_for_function('window.Liquid && !document.getElementById("send").disabled===false')
    check(page.locator('#welcome').is_visible(),'empty welcome screen')
    page.screenshot(path=str(SHOTS/'welcome-mobile.png'))
    page.locator('#model-button').click();check(page.locator('[data-model]').count()==4,'all four legacy profiles grouped and available')
    check('mesmos pesos' in page.locator('#sheet-body').inner_text().lower(),'base modes disclose same weights')
    check('Rust 1/5' in page.locator('#sheet-body').inner_text(),'experimental regression disclosed')
    page.screenshot(path=str(SHOTS/'models-mobile.png'));page.keyboard.press('Escape');check(not page.locator('#overlay').is_visible(),'Escape closes model dialog')
    page.locator('#reason-button').click();page.locator('[data-profile="extenso"]').click();check(page.locator('#reason-label').inner_text()=='Extenso','profile change via bridge event')
    page.locator('#message').fill('Me ajude a organizar uma lista em Python.');page.locator('#send').click();check(page.evaluate('calls.at(-1).type')=='send','send dispatches user request only')
    def event(e):page.evaluate('(e)=>Liquid.receive(e)',e)
    event({'type':'begin','text':'Me ajude a organizar uma lista em Python.'});event({'type':'stage','stage':'thinking','tokens':73});check('Pensando' in page.locator('.activity-label').last.inner_text(),'thinking is driven by runtime stage')
    event({'type':'thought','text':'Vou verificar o caso vazio e depois executar o exemplo.','forced':False});page.locator('.activity summary').click();check('caso vazio' in page.locator('.actual-thought').inner_text(),'only provided actual thought is shown')
    event({'type':'stage','stage':'searching','detail':'Documentação oficial de listas Python'});check('Buscando na web' in page.locator('.activity-label').last.inner_text(),'search state from real callback contract')
    event({'type':'tool','call':{'name':'search_web','arguments':{'query':'Documentação de listas Python'}},'observation':{'tool':'search_web','ok':True,'items':[{'title':'Estruturas de dados — Python','url':'https://docs.python.org/pt-br/3/tutorial/datastructures.html','snippet':'Métodos de listas e exemplos na documentação oficial.'}]}})
    check('1 fonte da web' in page.locator('.sources').inner_text(),'collapsible source count from returned observation')
    page.locator('.sources summary').click();page.locator('.source-link').click();check(page.evaluate('calls.at(-1).type')=='openLink','sources open through external-browser bridge')
    event({'type':'stage','stage':'python','detail':'Executando o código escolhido pelo modelo'});check('Executando Python' in page.locator('.activity-label').inner_text(),'Python execution state')
    event({'type':'tool','call':{'name':'run_python','arguments':{'code':'print(sorted([3, 1, 2]))'}},'observation':{'tool':'run_python','ok':True,'stdout':'[1, 2, 3]\n'}})
    text='Use **sorted** para criar uma nova lista ordenada.\n\n```python\nvalores = [3, 1, 2]\nordenados = sorted(valores)\nprint(ordenados)\n```\n\nO resultado conferido é `[1, 2, 3]`. A lista original fica preservada.'
    event({'type':'stream','text':text});event({'type':'finish','text':text,'reason':'stop','metrics':'Fixture de teste da UI · ponte simulada · nenhuma inferência real','forced':False})
    check(page.locator('.answer strong').inner_text()=='sorted','bold Markdown')
    check(page.locator('.answer .code-block').count()==1,'fenced code render with copy')
    page.locator('.answer .code-head button').click();check('valores = ' in page.evaluate('calls.at(-1).text'),'code copy preserves exact source')
    check(not page.locator('.activity').evaluate('(e)=>e.classList.contains("running")'),'activity stops after final callback')
    page.locator('.activity summary').click();page.locator('#scroll').evaluate('(e)=>e.scrollTop=e.scrollHeight');page.screenshot(path=str(SHOTS/'chat-mobile.png'))
    event({'type':'begin','text':'Entrada de teste'});bad='<img src=x onerror="window.pwned=1"><script>window.pwned=1</script> [x](javascript:alert(1))';event({'type':'stream','text':bad});event({'type':'finish','text':bad,'reason':'stop'})
    check(page.locator('.answer img,.answer script').count()==0,'untrusted HTML never interpreted')
    check(page.evaluate('window.pwned===undefined'),'script injection did not execute')
    check(page.locator('a[href^="javascript:"]').count()==0,'javascript links rejected')
    event({'type':'begin','text':'Parar'});page.locator('#send').click();check(page.evaluate('calls.at(-1).type')=='cancel','stop sends cancel, not a second prompt');event({'type':'finish','text':'','reason':'cancelled'});check('interrompida' in page.locator('.activity-label').last.inner_text(),'cancel is not labelled success')
    event(initial)
    for width,height in [(320,740),(393,852),(760,400),(1365,900)]:
        page.set_viewport_size({'width':width,'height':height});check(page.evaluate('document.documentElement.scrollWidth<=innerWidth'),f'no viewport overflow {width}x{height}')
    page.screenshot(path=str(SHOTS/'welcome-desktop.png'))
    page.set_viewport_size({'width':393,'height':852});page.locator('#menu').click();check(page.locator('#sidebar').is_visible(),'mobile conversation drawer');page.screenshot(path=str(SHOTS/'history-mobile.png'));page.locator('#history-search').fill('inexistente');check('Nenhuma conversa' in page.locator('#history').inner_text(),'history search filters saved titles')
    check(not errors,'no browser JavaScript errors')
    browser.close()
server.shutdown()
(H/'reports/browser_tests.json').write_text(json.dumps({'status':'passed','checks':len(checks),'details':checks,'scope':'bundled production HTML/CSS/JS in desktop Chromium, mocked Java bridge; no device or model inference','screenshots':str(SHOTS)},indent=2)+'\n');print('UI_BROWSER_CHECKS',len(checks))
