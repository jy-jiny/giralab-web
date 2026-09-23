# GiraLab Web

## 2026-09-23 · 판 종료 음악

원본 `2a4dce7c9ac28356de4b8ecf39a206d714fcdbf6`의 전체 Vite 빌드를 반영합니다. 결과 화면에 8초짜리 오리지널 곡 Experiment Complete가 한 번 재생되며, 기존 음악·음소거·기록·Google 로그인은 유지합니다. 새 판을 완료하면 다시 한 번 재생됩니다.

GitHub Actions 예산 해결 후 원본 APK/웹 빌드 `35802601488`이 성공했습니다. 웹 배포 워크플로는 게시 전후 기존 게임·계정 검사와 실제 결과 화면의 종료 음악/재도전 검사를 실행합니다. `site/source-build.json`에 원본 커밋·아티팩트와 파일 해시를 기록합니다. 실제 게시 완료 여부는 해당 배포 실행 결과를 확인합니다.


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

