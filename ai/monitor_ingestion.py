"""
ai/monitor_ingestion.py

Live CLI dashboard and log streamer for IP-SAKTI Sahayak data ingestion.
Run this script in any terminal to monitor progress in real time without stopping ingestion.
"""

import os
import sys
import time
from pathlib import Path
import yaml
from dotenv import load_dotenv

# Ensure UTF-8 output
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

root = Path(__file__).resolve().parent.parent
load_dotenv(root / "backend" / ".env")
load_dotenv(root / "ai" / ".env")

registry_path = root / "ai" / "ingestion_config" / "document_registry.yaml"

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def print_dashboard():
    while True:
        try:
            if not registry_path.exists():
                print("Waiting for registry file...")
                time.sleep(2)
                continue

            with open(registry_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            docs = data.get("documents", [])
            total = len(docs)
            validated = [d for d in docs if d.get("status") == "validated"]
            ingested = [d for d in docs if d.get("status") == "ingested"]
            analyzed = [d for d in docs if d.get("status") in ["analyzed", "chunked"]]
            pending = [d for d in docs if d.get("status") == "pending"]

            percent = (len(validated) / total * 100) if total else 0

            clear_screen()
            print("=" * 80)
            print(f"  IP-SAKTI Sahayak — Live Ingestion Monitor")
            print("=" * 80)
            print(f" Progress: [{len(validated)}/{total}] documents validated ({percent:.1f}%)")
            print(f" Status:   Validated: {len(validated)} | Ingesting/Chunking: {len(ingested) + len(analyzed)} | Pending: {len(pending)}")
            
            # Progress bar
            bar_len = 40
            filled = int(bar_len * len(validated) / max(1, total))
            bar = "█" * filled + "░" * (bar_len - filled)
            print(f" [{bar}] {percent:.1f}%")
            print("-" * 80)

            print(" Recently Ingested & Validated Documents:")
            for d in validated[-10:]:
                fn = d.get("source_filename")
                cat = d.get("doc_category")
                jur = d.get("jurisdiction")
                print(f"  ✔ [{jur}] {fn} ({cat})")

            if ingested or analyzed:
                active = (ingested + analyzed)[0]
                print("-" * 80)
                print(f" ⏳ Currently Processing: {active.get('source_filename')}")

            print("=" * 80)
            print(" Press Ctrl+C to exit monitor (Ingestion in background will continue).")
            
            time.sleep(2)
        except KeyboardInterrupt:
            print("\nMonitor exited. Ingestion is still running in background.")
            break
        except Exception as e:
            time.sleep(2)

if __name__ == "__main__":
    print_dashboard()
