# GiraLab Web

Public deployment target for the built GiraLab web app. Source code remains in the private repository.

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
