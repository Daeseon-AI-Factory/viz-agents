# 🚀 Deploy viz-core to Fly.io

> Where: https://your-viz-core.fly.dev (after deploy)
> Cost: $0 on free tier (3 shared VMs + 3GB volume)
> Time: 30 minutes first time

---

## 1. Install Fly CLI

```bash
# macOS
brew install flyctl

# verify
fly version
```

## 2. Sign up

```bash
fly auth signup
# follow prompts — credit card needed (won't charge unless you exceed free tier)
```

## 3. Launch (from viz-core/ directory)

```bash
cd viz-core
fly launch --no-deploy
# - app name: pick something unique (e.g. viz-core-daeseon)
# - region: nrt (Tokyo) for Korea, or pick yours
# - postgres / redis: NO (we use files)
# - copy fly.toml from this repo: YES (overwrite generated)
```

If `fly launch` overwrote your `fly.toml`, restore it:
```bash
git checkout fly.toml
```

## 4. Create persistent volumes (assets survive redeploys)

```bash
fly volumes create viz_data --size 1 --region nrt
fly volumes create viz_data_sessions --size 1 --region nrt
```

## 5. Set secrets (optional — only if using LLM routing)

```bash
fly secrets set ANTHROPIC_API_KEY="sk-ant-..."
```

> ⚠️ Never put the key in code, env files, or git.

## 6. Deploy

```bash
fly deploy
```

Wait ~3 minutes. Output ends with: `https://viz-core-daeseon.fly.dev`

## 7. Open

```bash
fly open
# or visit the URL directly
```

---

## After deploy

### Seed your library

Local → cloud:
```bash
# from your local machine
curl -X POST https://viz-core-daeseon.fly.dev/library/import \
  -H 'Content-Type: application/zip' \
  --data-binary @"$(curl -s http://localhost:8765/library/export -o /tmp/local.zip && echo /tmp/local.zip)"
```

Or upload via UI: open the deployed URL → 📚 Library → ⬆ Restore.

### Update

```bash
fly deploy
```

### Logs

```bash
fly logs
```

### Stop / scale

```bash
fly scale count 0  # stop entirely (no cost)
fly scale count 1  # restart
```

---

## Mobile access

Once deployed, your URL works from anywhere:
- Phone browser → bookmark → use it on the subway
- Add to home screen for app-like UX

---

## What's persistent

- ✅ `library/` (volume `viz_data`) — your assets
- ✅ `sessions/` (volume `viz_data_sessions`) — Claude Code session logs
- ❌ `usage_log.jsonl` (ephemeral — recreated on redeploy)
- ❌ `.local_key.txt` (use `fly secrets` instead)

---

## Cost (Fly.io free tier — 2026)

- 3 shared-cpu-1x VMs (256 MB)
- 3 GB persistent volume
- 160 GB outbound transfer

viz-core uses ~1 VM + ~10 MB volume per 1000 assets. Well under free tier.

If you exceed: ~$2/mo for additional VM, ~$0.15/GB-mo for volume.

---

## Troubleshooting

### App won't start
```bash
fly logs                # check error
fly ssh console         # shell into the VM
```

### Volume not mounting
```bash
fly volumes list
# ensure both viz_data and viz_data_sessions exist in same region
```

### CORS issues
viz-core's CORS allows all origins by default (for embedding). If issues, check
the X-Frame-Options header in server.py.

---

## Alternative: Railway (even simpler)

If Fly.io feels too CLI-heavy:

1. Push your repo to GitHub (done)
2. railway.app → New Project → Deploy from GitHub → select repo
3. Add a volume mounted at `/app/library`
4. Done — Railway auto-detects Dockerfile

Cost: $5 credit/mo (free for hobby), ~$5-10/mo when exceeded.
