"""Run from the folder containing vercel.json before pushing to Vercel."""
from pathlib import Path
import json
import sys

project = Path(__file__).resolve().parents[1]
config = json.loads((project / "vercel.json").read_text(encoding="utf-8"))
errors = []
for daemon_name, config_item in config.get("daemons", {}).items():
    dockerfile = project / config_item["root"] / config_item["entrypoint"]
    if not dockerfile.is_file():
        errors.append(f"{daemon_name}: Dockerfile missing: {dockerfile.relative_to(project)}")
    else:
        print(f"OK {daemon_name}: {dockerfile.relative_to(project)} exists")
required = ["worker/main.py", "worker/requirements.txt", "worker/messages/sri_lanka.txt"]
for name in required:
    if not (project / name).is_file():
        errors.append(f"Missing project file: {name}")
if errors:
    for message in errors:
        print("ERROR", message)
    sys.exit(1)
print("Local project structure verified. Verify your GitHub repository and Vercel Root Directory match this structure.")
