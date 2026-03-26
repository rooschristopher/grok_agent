#!/usr/bin/env python3
import time
import json
import os
from pathlib import Path
from datetime import datetime
import hashlib

WORK_ITEMS_ROOT = Path.home() / 'work_items'
STATE_FILE = Path.home() / 'work_items_watcher_state.json'

def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

def get_hash(file_path):
    if file_path.exists():
        h = hashlib.md5()
        h.update(file_path.read_bytes())
        return h.hexdigest()
    return None

print("👀 Work Item Watcher - ~/work_items")
print("Detects new dirs or changes to OBJECTIVE.md")
print("Press Ctrl+C to stop.")

state = load_state()
last_seen = state.get('last_seen', {})

try:
    while True:
        changes = []
        for item_dir in WORK_ITEMS_ROOT.iterdir():
            if not item_dir.is_dir():
                continue
            id_file = item_dir / 'id.txt'
            obj_file = item_dir / 'OBJECTIVE.md'
            hist_file = item_dir / 'HISTORY.md'
            if not id_file.exists() or not obj_file.exists():
                continue  # Valid work item?

            item_id = id_file.read_text().strip()
            if item_id != item_dir.name:
                continue

            # Check for changes
            obj_hash = get_hash(obj_file)
            last_hash = last_seen.get(item_dir.name, {}).get('obj_hash')
            if obj_hash != last_hash:
                # Check if done
                if hist_file.exists() and 'FINAL WORK ITEM COMPLETE' in hist_file.read_text():
                    print(f"✅ {item_dir.name}: Already complete (FINAL detected)")
                else:
                    changes.append(item_dir.name)
                    print(f"🚨 CHANGE DETECTED in {item_dir.name} (OBJECTIVE.md changed)")
                    print(f"   ID: {item_id}")
                    print(f"   Suggested spawn goal: 'Process ~/work_items/{item_dir.name} ...'")
                    print()

            # Update seen
            last_seen.setdefault(item_dir.name, {})['obj_hash'] = obj_hash

        if changes:
            state['last_seen'] = last_seen
            save_state(state)

        time.sleep(5)  # Poll every 5s
except KeyboardInterrupt:
    print("\\n👋 Watcher stopped. State saved.")
    save_state({'last_seen': last_seen})
