# GiraLab Web

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
