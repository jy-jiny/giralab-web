# GiraLab Web

## 2026-09-23 · Google 로그인 확인과 이전 인증 폐기 완료

사용자가 공개 웹에서 실제 Google 재로그인과 기존 기록 복구 성공을 확인했다. 11:13 UTC 운영 전환으로 이전 인증 RPC 자격·공유 인증 bridge·DB의 이전 HMAC 키 복사본을 폐기했다. 기존 계정·점수·도감·세션 9개 표의 전후 전체 지문이 일치했다. Netlify의 원본 HMAC 키와 새 독립 자격은 유지한다.

새 호스트의 900초 토큰 발급·갱신·재사용 차단·HttpOnly 쿠키·CSRF 검사를 다시 통과했다. 이전 Supabase 인증 주소는 410 UPDATE_REQUIRED를 반환하고 게임 서버는 정상이다. `source-build.json`의 전환 상태만 갱신하며 원본 빌드 커밋과 20개 파일 해시는 유지한다. 아래 절은 이전 배포 이력이다. Android 실기기 설치 확인과 공유 DB 관리자 침해 위험은 별개다.


## 2026-09-23 · 인증 서버 Netlify 분리

2026-09-23 [배포 35848467623](https://github.com/jy-jiny/giralab-web/actions/runs/35848467623)이 성공했다. 게시 전후 계정·게임·로딩·음악·결과 화면 회귀 검사가 모두 통과했고 실제 공개 metadata의 새 인증 URL을 확인했다. 원본 배포 기록은 `jy-jiny/giralab`의 `docs/game/evidence/2026-09-23-auth-isolation.json`이다. 실제 Google 재로그인과 이전 인증 키 폐기는 여전히 별도 확인 단계다.

검증된 원본 `1ddb385dd405bc7bf10a8331fa12b9796689b7db`의 전체 Vite 아티팩트를 반영한다. Google 확인과 쿠키/토큰 갱신은 `https://giralab-auth.netlify.app`에서 처리한다. 기존 게임 서버 주소·계정·점수·도감·음량·종료 음악은 유지한다. 웹 인증 쿠키의 호스트가 바뀌어 Google 로그인이 한 번 더 필요할 수 있다. 이전 인증 자격 폐기는 실제 Google 재로그인 확인 후 진행하며, 이 단계에서 완전한 비밀키 격리 완료로 표시하지 않는다.

CI 아티팩트 ZIP SHA-256 및 원본 tree 일치, 빌드 20개 파일과 기존 이미지/음악 해시를 확인했다. 계정 UI fixture는 배포 metadata의 정확한 게임·인증 API를 가로채며 운영 계정/점수는 쓰지 않는다. 기존 게시 전후 회귀 검사를 유지한다. 최종 게시 결과와 실계정 로그인은 별도 확인 사항이다.


## 2026-09-23 · 짧은 토큰과 웹 쿠키

검증한 원본 `66ec5f80ac7aec5866fbd588eaf85ed6eee376db`의 전체 Vite 빌드를 적용한다. 기존 Supabase의 `giralab-auth`에서 15분 게임 토큰·자동 갱신·HttpOnly/Secure/Partitioned 쿠키를 제공한다. 30일 미사용 또는 Google 확인 후 90일에 재인증하며 계정과 기록은 유지한다. 기존 365일 토큰은 배포 후 7일 내 한 번만 자동 이행한다. 인증 환경과 비밀키까지 격리하는 작업은 후속이다.

게시 전후 게임·계정 검사를 유지한다. 기존 UI fixture에 단기 세션 전송 어댑터를 추가했으며 실제 쿠키·갱신·만료·동시 요청은 원본의 브라우저/PG17 검사에서 별도로 검증했다. 개인 Google 계정 선택과 실기기 조작은 자동 검사와 구분한다.


운영 게시 작업은 `deploy.yml` 한 곳에서 전체 빌드와 게시 전후 회귀 검사를 실행한다. 이전 대시보드·테마 아트 단독 게시기는 `source-build.json`에 새 인증 주소가 있으면 실행을 건너뛰어 과거 번들로의 되돌림을 방지한다. 현재 게시의 계정·게임 검사 조건은 유지한다.

## 2026-09-23 · 판 종료 음악

원본 `2a4dce7c9ac28356de4b8ecf39a206d714fcdbf6`의 전체 Vite 빌드를 반영합니다. 결과 화면에 8초짜리 오리지널 곡 Experiment Complete가 한 번 재생되며, 기존 음악·음소거·기록·Google 로그인은 유지합니다. 새 판을 완료하면 다시 한 번 재생됩니다.

GitHub Actions 예산 해결 후 원본 APK/웹 빌드 `35802601488`이 성공했습니다. 웹 배포 워크플로는 게시 전후 기존 게임·계정 검사와 실제 결과 화면의 종료 음악/재도전 검사를 실행합니다. `site/source-build.json`에 원본 커밋·아티팩트와 파일 해시를 기록합니다. [최종 배포 35805200578](https://github.com/jy-jiny/giralab-web/actions/runs/35805200578)이 성공했으며 게시 전후 게임·계정·로딩·오디오·결과 검사가 모두 통과했습니다. 실제 공개 URL에서 8초/반복 없음/판당 한 번/재도전 후 재생/기존 게임 음악 중단을 확인했습니다. 실계정 Google 인증과 실기기 청음은 별도입니다.

첫 배포 `35804019836`은 게시 전 결과 음악 검증과 GitHub Pages 게시에 성공했으나, 게시 후 로딩/음량 검사에서 메인 복귀 직후 옵션 창 확인이 실패했습니다. 검사는 닫히는 Radix 대화상자와 오버레이가 제거되고 메인 화면이 표시된 뒤 메인의 옵션 버튼을 누르도록 보완했습니다. 음량/음소거/오디오 미지원에 대한 기존 단언은 유지하며, 실패 시 화면과 대화상자 상태를 남깁니다. 보완 후 동일한 전체 게시 전후 검사를 통과했습니다. 검증 증거는 해당 실행의 `giralab-e5-live-verification` 아티팩트에 보관합니다.


The 2026-09-22 web Google login rollout is documented in [WEB_GOOGLE_LOGIN_20260922.md](WEB_GOOGLE_LOGIN_20260922.md). The original API URL and existing records are preserved; publication and actual Google account verification are separate.

Public deployment target for the built GiraLab web app. Source code remains in the private repository.

The 2026-09-22 Google-first release requires Google proof before a new nickname,
restores an existing account automatically, and preserves server records on logout.
The original `giralab-game` API address remains unchanged so saved installation
credentials, account journals and progress keep their existing namespace.
`site/source-build.json` records the exact source tree, file hashes, provider readiness
and the separate status of actual Google-account verification. This release does not
reset server data or publish an app to a store.

Before and after publication, the account suite checks ten isolated login/account
scenarios. Gameplay regressions use a saved linked-player fixture and private-backup
responses, preserving the existing layout, audio, rules, codex and result checks.
Loading checks exercise Google-first entry before nickname input and retain the
same audio element through verified nickname creation. Every game API and Google
credential in these automated checks is a fixture; no production account or score
is created. The earlier release history below describes previous publications.

The 2026-09-21 results release adds the end-of-game report (tier counts, score chart,
final score and image sharing) from the shared app UI. `site/source-build.json`
identifies the source revision and hashes every file in the full Vite build.
Existing loading art, Kitchen Rush music, rules and player storage remain compatible.

Publication runs the existing gameplay, layout, audio and codex checks, plus
`scripts/verify-run-result.py`, before and after GitHub Pages deployment. Game API
requests in browser checks use isolated fixtures; no production scores are written.
The old regression suites inject `scripts/browser-game-driver.js` in the test
runner only. It is never shipped in `site/`; the new result test uses actual DOM
controls and verifies that the release registers no AI game-control tools.

The first publication succeeded, but the live mythic-effect check exposed a test
observer race: React's previous render can still have a null animation object.
The driver now reads the stable presentation timer ref and validates its hook
anchor. Gameplay assertions remain unchanged; the published build is unchanged.


