"""Read-only mobile codex regression with isolated API fixtures and stable recipe IDs."""
import argparse, json, os, re, shutil, subprocess, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

VERSION='1.6.1'
ROWS=[
 ('classic','클래식 버거','normal','가장 기본적인 버거부터 떠올려보세요.'),
 ('cheese','치즈 버거','normal','노란 재료 하나가 맛의 포인트예요.'),
 ('green','그린 버거','normal','초록 재료가 한 번 끼어들어요.'),
 ('bacon','베이컨 버거','normal','짭짤하고 바삭한 재료가 포인트예요.'),
 ('double-patty','더블 패티 버거','normal','이름 그대로 패티를 넉넉히 써보세요.'),
 ('double','더블 치즈 버거','advanced','치즈가 한 장으로는 부족해요.'),
 ('bacon-cheese','베이컨 치즈 버거','advanced','바삭한 재료가 노란 재료보다 먼저 와요.'),
 ('cheese-melt','치즈 멜트 버거','advanced','치즈가 가운데 재료를 감싸는 느낌이에요.'),
 ('garden-stack','가든 스택 버거','advanced','초록 재료를 평소보다 더 활용해보세요.'),
 ('smoky-green','스모키 그린 버거','advanced','훈연향과 초록색이 같이 필요해요.'),
 ('bacon-first','베이컨 퍼스트 버거','advanced','이름처럼 바삭한 재료를 아주 앞쪽에 둬보세요.'),
 ('green-cheese','그린 치즈 버거','advanced','초록 다음 노란 재료가 힌트예요.'),
 ('cheese-bacon-stack','치즈 베이컨 스택','advanced','고소함과 바삭함을 한 버거에 담아보세요.'),
 ('double-bacon','더블 베이컨 버거','advanced','바삭한 재료가 한 번으로는 부족해요.'),
 ('cheese-mad','치즈에 미친 햄버거','rare','치즈가 핵심. 정말 많이 들어가요.'),
 ('meat-monster','고기 괴물 버거','rare','고기 계열 재료로 속을 꽉 채워보세요.'),
 ('green-monster','초록 괴물 버거','rare','초록 재료 비중이 아주 높아요.'),
 ('bacon-bomb','베이컨 폭탄 버거','rare','베이컨을 아끼면 안 돼요.'),
 ('forbidden-seven','금단의 7층 버거','mythic','일곱 층의 금단 실험. 빵 사이를 다섯 장의 베이컨으로만 채워보세요.'),
]
LABELS={'normal':'일반 조합','advanced':'고급 조합','rare':'전설 조합'}
COLORS={'normal':'rgb(226, 232, 240)','advanced':'rgb(29, 78, 216)','rare':'rgb(250, 204, 21)'}

LABELS['mythic']='신화 조합'
COLORS['mythic']='rgb(107, 33, 168)'


def verify(base,out):
    out.mkdir(parents=True,exist_ok=True)
    report={'game_version':VERSION,'base_url':base,'network':'Isolated API fixtures; no production writes','tests':[]}
    states={'undiscovered':['classic'],'discovered':[r[0] for r in ROWS],'mixed':['classic','double-patty','bacon-first','cheese-mad']}
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium') or None,args=['--no-sandbox','--disable-dev-shm-usage'])
        for width,height in [(360,640),(390,844),(412,915)]:
            for state,unlocked in states.items():
                ctx=browser.new_context(viewport={'width':width,'height':height},device_scale_factor=2,is_mobile=True,has_touch=True)
                page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.set_default_timeout(20000)
                def fixture(route):
                    name=route.request.url.split('/api/')[-1].split('?')[0]
                    data={'player':{'id':'codex-order-qa','nickname':'정렬검증'}} if name=='player' else {'entries':[],'me':None} if name=='leaderboard' else {'unlocked':unlocked,'bestScore':0}
                    route.fulfill(status=200,content_type='application/json',body=json.dumps(data))
                page.route('**/api/**',fixture)
                page.goto(base+'?codex-order='+VERSION,wait_until='domcontentloaded')
                page.locator('.home-screen').wait_for(state='visible')
                expect(page.locator('.home-version')).to_have_text('GiraLab · '+VERSION)
                page.get_by_role('button',name='옵션',exact=True).click()
                page.get_by_role('button',name=re.compile('레시피 도감')).click()
                cards=page.locator('.recipe-card');expect(cards).to_have_count(len(ROWS))
                expect(page.locator('.recipe-card.locked')).to_have_count(len(ROWS)-len(unlocked))
                ids=cards.evaluate_all('(nodes)=>nodes.map(el=>el.dataset.recipeId)')
                assert ids==[r[0] for r in ROWS],ids
                headings=page.locator('.recipe-group-heading')
                expect(headings).to_have_count(4)
                expect(headings.locator('span')).to_have_text(['일반','고급','전설','신화'])
                expect(headings.locator('small')).to_have_text(['5종','9종','4종','1종'])
                expected_nodes=[]
                for i,(rid,name,tier,hint) in enumerate(ROWS):
                    if i in (0,5,14,18):expected_nodes.append('group:'+tier)
                    expected_nodes.append('card:'+rid)
                    card=cards.nth(i)
                    expect(card).to_have_attribute('data-recipe-tier-card',tier)
                    expect(card.locator('.recipe-card-top span').first).to_have_text(f'NO. {i+1:02}')
                    expect(card.locator('.recipe-heading h3')).to_have_text(name)
                    badge=card.locator('.recipe-heading .recipe-tier-badge')
                    expect(badge).to_have_count(1);expect(badge).to_have_text(LABELS[tier])
                    expect(badge).to_have_attribute('data-recipe-tier',tier)
                    expected_slow='슬로우 없음' if tier=='normal' else '슬로우 3초' if tier=='advanced' else '슬로우 6초' if tier=='mythic' else '슬로우 4초'
                    assert expected_slow in badge.get_attribute('aria-label')
                    assert badge.evaluate('(el)=>getComputedStyle(el).backgroundColor')==COLORS[tier]
                    geometry=card.evaluate('''el=>{
                      const c=el.getBoundingClientRect(),t=el.querySelector('.recipe-heading h3').getBoundingClientRect(),b=el.querySelector('.recipe-tier-badge').getBoundingClientRect();
                      return {below:b.top>=t.bottom+3,within:b.left>=c.left-1&&b.right<=c.right+1,titleWithin:t.left>=c.left-1&&t.right<=c.right+1};
                    }''')
                    assert all(geometry.values()),(rid,geometry)
                    if rid in unlocked:
                        expect(card.locator('.recipe-order')).to_have_count(1)
                        expect(card.locator('.recipe-hint-toggle')).to_have_count(0)
                    else:
                        expect(card.locator('.recipe-order')).to_have_count(0)
                        expect(card.locator('.recipe-hint-toggle')).to_have_count(1)
                        expect(card.locator('.recipe-hint-panel')).to_have_count(1)
                        expect(card.locator('.recipe-hint-panel')).to_be_hidden()
                        expect(card.locator('.recipe-hint-panel span')).to_have_text(hint)
                nodes=page.locator('.recipe-grid').evaluate('''el=>[...el.children].map(n=>n.dataset.recipeId?'card:'+n.dataset.recipeId:'group:'+n.dataset.recipeGroupTier)''')
                assert nodes==expected_nodes,nodes
                assert page.locator('.recipe-grid').evaluate('(el)=>el.scrollWidth<=el.clientWidth+1')
                assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1')
                suffix=f'{width}x{height}-{state}'
                page.screenshot(path=str(out/f'codex-{suffix}-normal.png'))
                cards.nth(4).scroll_into_view_if_needed()
                page.screenshot(path=str(out/f'codex-{suffix}-double-patty.png'))
                if 'double-patty' not in unlocked:
                    toggle=cards.nth(4).locator('.recipe-hint-toggle');toggle.click()
                    expect(toggle).to_have_attribute('aria-expanded','true')
                    expect(cards.nth(4).locator('.recipe-hint-panel')).to_be_visible()
                    toggle.click();expect(toggle).to_have_attribute('aria-expanded','false')
                headings.nth(1).scroll_into_view_if_needed()
                page.screenshot(path=str(out/f'codex-{suffix}-advanced.png'))
                headings.nth(2).scroll_into_view_if_needed()
                page.screenshot(path=str(out/f'codex-{suffix}-legendary.png'))
                # Reopening must not duplicate hints or restore the old index-based order.
                page.get_by_role('button',name='옵션',exact=True).click()
                page.get_by_role('button',name=re.compile('레시피 도감')).click()
                expect(page.locator('.recipe-card')).to_have_count(len(ROWS))
                expect(page.locator('.recipe-hint-toggle')).to_have_count(len(ROWS)-len(unlocked))
                expect(page.locator('[data-recipe-id="double-patty"] h3')).to_have_text('더블 패티 버거')
                assert page.locator('.recipe-card').evaluate_all('(els)=>els.map(el=>el.dataset.recipeId)')==ids
                meta=ctx.request.get(base+'source-build.json?codex-order='+VERSION).json()
                assert meta['game_version']==VERSION and meta['codex_grouped'] is True
                assert meta['recipe_badge_position']=='below-name' and meta['rare_display_name']=='전설'
                assert meta['board_validity_max_tier']=='advanced' and meta['automatic_board_hints'] is False
                assert not errors,errors
                report['tests'].append({'viewport':[width,height],'discovery':state,'ids':ids,'groups':['일반','고급','전설','신화'],'badgesBelowNames':len(ROWS),'correctNamesAndHints':True,'reopenStable':True,'page_errors':errors})
                ctx.close()
        browser.close()
    (out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--site',default='site');parser.add_argument('--url');parser.add_argument('--out',default='codex-order-proof');args=parser.parse_args()
    if args.url:verify(args.url.rstrip('/')+'/',Path(args.out))
    else:
        with tempfile.TemporaryDirectory() as root:
            os.symlink(Path(args.site).resolve(),Path(root)/'giralab-web',target_is_directory=True)
            server=subprocess.Popen(['python3','-m','http.server','4177','--bind','127.0.0.1','--directory',root],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            try:time.sleep(.5);verify('http://127.0.0.1:4177/giralab-web/',Path(args.out))
            finally:server.terminate();server.wait(timeout=5)
