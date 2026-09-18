"""Observe loading audio without synthetic activation. All game APIs use fixtures."""
import argparse,json,os,shutil,subprocess,tempfile,time
from pathlib import Path
from playwright.sync_api import sync_playwright,expect

VERSION='1.7.1'
HOOK='''window.__gameTools={};Object.defineProperty(document,'modelContext',{configurable:true,value:{registerTool(t){window.__gameTools[t.name]=t}}});
window.__audioContexts=[];const RealAudioContext=window.AudioContext;
if(RealAudioContext)window.AudioContext=class extends RealAudioContext{constructor(...args){super(...args);window.__audioContexts.push(this)}};
'''
FORBIDDEN='.audio-enable,button[aria-label="배경음악 켜기"],button[aria-label="배경음악 끄기"],.sound-setting,[role="slider"]'

def verify(base,out):
 out.mkdir(parents=True,exist_ok=True)
 report={'version':VERSION,'base_url':base,'api':'Isolated fixtures; no production writes','cases':[]}
 cases=[('loading-default',360,640,'no-user-gesture-required',None,False,False),('loading-default',390,844,'no-user-gesture-required',None,False,False),('loading-default',412,915,'no-user-gesture-required',None,False,False),('first-visit-blocked',390,844,'document-user-activation-required',None,False,False),('nickname-registration',390,844,'no-user-gesture-required',None,True,False),('saved-muted',390,844,'no-user-gesture-required',0,False,False),('saved-volume',360,640,'no-user-gesture-required',20,False,False),('audio-unavailable',390,844,'no-user-gesture-required',None,False,True)]
 with sync_playwright() as p:
  executable=shutil.which('google-chrome') or shutil.which('chromium')
  for label,width,height,policy,saved,new_player,unsupported in cases:
   browser=p.chromium.launch(executable_path=executable,args=['--no-sandbox','--disable-dev-shm-usage','--disable-features=PreloadMediaEngagementData,MediaEngagementBypassAutoplayPolicies','--autoplay-policy='+policy])
   ctx=browser.new_context(viewport={'width':width,'height':height},is_mobile=True,has_touch=True)
   init=HOOK
   if saved is not None:init+=f"localStorage.setItem('burger-lab-music-volume','{saved}');"
   if unsupported:init+='window.AudioContext=undefined;'
   ctx.add_init_script(init)
   page=ctx.new_page();page.set_default_timeout(15000);pending=[];errors=[];page.on('pageerror',lambda e:errors.append(str(e)));first=[True]
   def fixture(route):
    name=route.request.url.split('/api/')[-1].split('?')[0]
    if name=='player' and route.request.method=='GET' and first[0]:first[0]=False;pending.append(route);return
    data={'player':{'id':'loading-audio-qa','nickname':'음악검증'}} if name=='player' else {'entries':[],'me':None} if name=='leaderboard' else {'unlocked':['classic'],'bestScore':0}
    if name=='progress' and route.request.method=='POST':data=route.request.post_data_json
    route.fulfill(status=200,content_type='application/json',body=json.dumps(data))
   page.route('**/api/**',fixture)
   page.goto(base+'?loading-audio='+VERSION,wait_until='domcontentloaded')
   cdp=ctx.new_cdp_session(page)
   def read(expr):
    result=cdp.send('Runtime.evaluate',{'expression':expr,'returnByValue':True,'userGesture':False})
    assert 'exceptionDetails' not in result,result
    return result['result'].get('value')
   def state():return read('window.__gameTools.get_audio_state?.execute({})')
   for _ in range(100):
    initial=state()
    if initial and pending:break
    page.wait_for_timeout(40)
   assert initial and pending,(label,initial)
   assert read('!!document.querySelector(".giralab-boot")'),'Probe must occur during loading'
   assert read('navigator.userActivation.hasBeenActive') is False,'Probe must not unlock audio'
   assert read('document.querySelectorAll("audio").length')==1
   assert not read(f'!!document.querySelector({json.dumps(FORBIDDEN)})'),'No sound controls on loading'
   assert initial['musicVolume']==(45 if saved is None else saved),initial
   if unsupported:assert initial['context']=='uninitialized' and not initial['labPlaying']
   elif policy=='document-user-activation-required':assert initial['context']=='suspended' and not initial['labPlaying']
   else:assert initial['context']=='running' and initial['labPlaying']==(saved!=0),initial
   read('window.__keptMedia=document.querySelector("audio");true')
   time0=read('window.__audioContexts[0]?.currentTime')
   pending.pop().fulfill(status=200,content_type='application/json',body=json.dumps({'player':None if new_player else {'id':'loading-audio-qa','nickname':'음악검증'}}))
   selector='.nickname-screen' if new_player else '.home-screen'
   for _ in range(100):
    if read(f'!!document.querySelector({json.dumps(selector)})'):break
    page.wait_for_timeout(40)
   assert read(f'!!document.querySelector({json.dumps(selector)})')
   assert read('navigator.userActivation.hasBeenActive') is False
   assert read('document.querySelector("audio")===window.__keptMedia')
   assert read('window.__audioContexts.length')==(0 if unsupported else 1)
   if not unsupported and policy=='no-user-gesture-required':assert read('window.__audioContexts[0].currentTime')>time0
   if new_player:
    page.locator('#nickname').fill('연구원음악');page.get_by_role('button',name='이 이름으로 시작').click();expect(page.locator('.home-screen')).to_be_visible()
    assert read('window.__audioContexts.length')==1
    assert read('document.querySelector("audio")===window.__keptMedia')
   expect(page.locator('.home-version')).to_have_text('GiraLab · '+VERSION)
   expect(page.locator(FORBIDDEN)).to_have_count(0)
   if policy=='document-user-activation-required':
    assert not state()['labPlaying'];page.locator('.home-version').click()
    page.wait_for_function('window.__gameTools.get_audio_state.execute({}).labPlaying')
   page.screenshot(path=str(out/f'{label}-{width}-home.png'))
   if page.locator('[data-theme-select=burger]').count(): page.locator('[data-theme-select=burger]').click()
   page.locator('.home-play').click()
   if unsupported or saved==0:assert not state()['gamePlaying']
   else:
    page.wait_for_function('window.__gameTools.get_audio_state.execute({}).gamePlaying');assert state()['track']=='Kitchen Rush'
   expect(page.locator(FORBIDDEN)).to_have_count(0)
   page.get_by_role('button',name='메인으로',exact=True).click()
   if not unsupported and saved!=0:
    page.wait_for_function('window.__gameTools.get_audio_state.execute({}).labPlaying');assert not state()['gamePlaying']
    page.evaluate('window.dispatchEvent(new Event("burger-native-pause"))');assert not state()['labPlaying']
    page.evaluate('window.dispatchEvent(new Event("burger-native-resume"))');page.wait_for_function('window.__gameTools.get_audio_state.execute({}).labPlaying')
   page.get_by_role('button',name='옵션',exact=True).click()
   expect(page.locator('.settings-dialog .sound-setting')).to_have_count(1)
   expect(page.locator('.settings-dialog [role="slider"]')).to_have_count(2)
   expect(page.locator('.audio-enable')).to_have_count(0)
   if unsupported:expect(page.locator('.settings-dialog .audio-setting-status')).to_be_visible()
   else:
    effects=state()['effectsVolume']
    page.get_by_role('button',name='배경음악 켜기' if state()['musicVolume']==0 else '배경음악 끄기',exact=True).click()
    assert state()['musicVolume']==(45 if saved==0 else 0);assert state()['effectsVolume']==effects
    assert page.evaluate("localStorage.getItem('burger-lab-music-volume')")==str(state()['musicVolume'])
    page.get_by_role('button',name='배경음악 끄기' if saved==0 else '배경음악 켜기',exact=True).click()
    assert state()['musicVolume']==(0 if saved==0 else 45)
    page.get_by_role('button',name='효과음 끄기',exact=True).click();assert state()['effectsVolume']==0
    page.get_by_role('button',name='효과음 켜기',exact=True).click();assert state()['effectsVolume']==65
   page.screenshot(path=str(out/f'{label}-{width}-settings.png'))
   page.get_by_role('button',name='닫기',exact=True).click();expect(page.locator(FORBIDDEN)).to_have_count(0)
   assert read('document.querySelector("audio")===window.__keptMedia')
   assert read('window.__audioContexts.length')==(0 if unsupported else 1)
   assert not errors,errors
   report['cases'].append({'case':label,'viewport':[width,height],'autoplay_policy':policy,'initial_loading_audio':initial,'sameMediaAndMixer':True,'gearOnlyControls':True,'errors':errors})
   ctx.close();browser.close()
 (out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--site',default='pages-dist');parser.add_argument('--url');parser.add_argument('--out',default='loading-audio-proof');args=parser.parse_args()
 if args.url:verify(args.url.rstrip('/')+'/',Path(args.out))
 else:
  with tempfile.TemporaryDirectory() as root:
   os.symlink(Path(args.site).resolve(),Path(root)/'giralab-web',target_is_directory=True)
   server=subprocess.Popen(['python3','-m','http.server','4180','--bind','127.0.0.1','--directory',root],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   try:time.sleep(.3);verify('http://127.0.0.1:4180/giralab-web/',Path(args.out))
   finally:server.terminate();server.wait(timeout=5)
