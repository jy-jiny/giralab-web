# E5 account delivery · 2026-09-22

Source: jy-jiny/giralab PR #10, commit 2c032cc21643d854ef7aac5573b0fd1b853cffb6.
The complete source tree was verified before building. Vite output names match source CI run 35676748335. Every published build file is SHA-256 pinned in site/source-build.json.

The account UI preserves the existing owner and records, supports email linking/recovery, and requires a separate deletion confirmation. A lost deletion response resumes using its durable request ID. The external entry is delete-account.html.

Email readiness remains disabled until SMTP, templates and actual delivery are verified. Existing guests can delete their own account without email. No production users, mail, scores or deletion requests are created by tests.

Deployment gates retain the existing gameplay, artwork, sound, record and layout tests and add account UI cases against isolated API fixtures. PRs validate without publishing. Optional screenshots use one-day retention and cannot fail a successfully validated release. The required GitHub Pages artifact and publication still must succeed. Current account-wide artifact quota is being diagnosed; no existing artifacts have been deleted.
