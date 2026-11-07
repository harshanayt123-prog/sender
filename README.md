# Telegram announcement worker on Vercel Daemons (corrected flat-root release)

## Fix for INVALID_DAEMON_ROOT

**This ZIP has NO enclosing folder.** When extracted, `vercel.json` and `worker/` must be next to each other in the **top level of your GitHub repository**. Upload *all* extracted content, preserving `worker/Dockerfile` with that exact spelling and capital `D`.

Correct GitHub repository contents:

```text
<repository root>/
  vercel.json
  .vercelignore
  .gitignore
  .env.example
  README.md
  worker/
    Dockerfile
    .dockerignore
    main.py
    requirements.txt
    messages/
      sri_lanka.txt
      india.txt
      ...
  local_tools/
    check_vercel_layout.py
    ...
```

Vercel Project Settings → Build and Deployment → **Root Directory**: leave blank / use repository root. It must NOT be `worker`, `telegram-vercel-daemon`, or another subfolder. This is a current limitation of Daemons (see https://vercel.com/docs/daemons). Set **Framework Preset: Other**, and remove old custom Build and Output commands. Deploy **Production**, not Preview.

`vercel.json` has `root: "worker/"` and `entrypoint: "Dockerfile"`, which must resolve to **`worker/Dockerfile`** within the repository. See https://vercel.com/docs/daemons/config-reference.

If you use Git locally, from the directory containing `vercel.json`:

```bash
python local_tools/check_vercel_layout.py
git add vercel.json worker/ .vercelignore .gitignore README.md .env.example local_tools/
git ls-files worker/Dockerfile
# If that last command prints nothing, check your .gitignore and run:
git add -f worker/Dockerfile
git commit -m "Fix Vercel daemon source path"
git push
```

In GitHub's web interface, confirm that `worker/Dockerfile` is visible **in the branch connected to Vercel**. If the Vercel project has been pointed at a nested Root Directory, clear that setting before redeploying. Changing the ZIP alone cannot override incorrect settings on Vercel.

## Running

1. Set `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_SESSION` and the permitted group IDs in Vercel's **Production environment variables**; copy names from `.env.example`. **Never commit actual credentials.**
2. Leave `DRY_RUN=true` to check group selection and logs without sending messages.
3. Deploy to Production (`vercel --prod` from repository root, or a push to your production Git branch).
4. Check Vercel Project Logs for the `telegram-worker` daemon. After confirming permission to post to the configured groups, set `DRY_RUN=false` and redeploy.

The project is a **container daemon**, not a Python HTTP Function. Do not create a Flask/FastAPI `app` or route requests to `main.py`. This release retains the existing continuous Telethon loop, country/language mapping, and message templates. Blank message templates are skipped. Only use this in groups where automated announcements are explicitly allowed. Telegram account restrictions must be respected.

## Local checks

```bash
python local_tools/check_vercel_layout.py
# Docker Desktop must be installed and running:
docker build -t telegram-worker ./worker
# Supply environment variables in a local .env file (never commit):
docker run --rm --env-file .env telegram-worker
```

`vercel dev` does not run daemons. Daemons are available only on production deployments during this beta. Hobby has a small daemon quota; continuous free 24/7 operation is not available.
