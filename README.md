# Sentient Artifacts TUI

Textual dashboard for the Sentient Artifacts bot swarm. My bot itself is
private; this repo is API-only because I wanted to share the TUI. It connects
to the FastAPI server exposed by the main bots repository.
I may release the bot code in the future, but for now it is private.

## Quickstart

1. Install dependencies:

```bash
uv sync
```

2. Run the TUI (Connected to local Bot Manager):

```bash
sentient-tui --url http://localhost:8765
```

3. **Alternatively**, run the TUI in view-only mode using the official Artifacts MMO API:

```bash
sentient-tui --token YOUR_GAME_TOKEN
```

## Notes

- The API server must be running in the main (private) bots repo.
- Sprites live in `skins/` at the repo root.
