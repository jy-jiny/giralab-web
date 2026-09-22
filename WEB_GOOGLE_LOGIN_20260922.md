# Web Google login rollout — 2026-09-22

The public web starts with Google sign-in. A returning Google account restores its existing nickname and records; only a new account chooses a nickname. A valid saved installation session enters automatically. Logout disconnects this browser and preserves server records, other devices and audio preferences.

The full Vite build is from original PR #12, source commit `8209999307c102b2c200cc3e71b96812218adf8a`, tree `419e9418126f4b9a26277a5f1aff30ae024a6504`. `site/source-build.json` records every current build file hash. Approved loading art, music, rules and recipes are unchanged. The old hashed assets are retained for already-open pages; the new HTML references only the verified new build.

The API remains `https://tqqgnrfklhmxwsphjera.supabase.co/functions/v1/giralab-game` to preserve URL-scoped local progress and interrupted account journals. Its server release uses the existing additive login-first migration; this rollout does not reset or migrate records. The Android trial function continues using the same database.

Google Web OAuth configuration must allow JavaScript origin `https://jy-jiny.github.io` (no path). This integration uses a popup and JavaScript ID-token callback, so it does not require a redirect URI. The client secret is never included in this repository. The console's origin allowlist and actual Google account login cannot be verified by fixture tests.

Validation: source TypeScript/documentation/shared-boundary checks and 33 isolated Google SDK recovery checks passed locally. The deployment workflow verifies the first-login, nickname, automatic entry, logout and existing account flows, plus the preserved layout/game/audio/codex/result behavior before publishing. These tests intercept all game API/Google credential traffic and write no production test records. Final workflow status is the source of truth for publication.

Android is the first planned store release. Publishing this web test does not submit an app to a store or configure iOS OAuth.
