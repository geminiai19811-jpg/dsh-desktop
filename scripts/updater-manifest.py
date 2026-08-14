#!/usr/bin/env python3
"""Build the Tauri updater `latest.json` manifest (used by the release workflow).

Avoids inline heredocs in CI (whose leading indentation breaks bash).

Subcommands:
  fragment <platform_key> <url> <sig_file> <out_file>
      Write a single-platform fragment: {platform_key: {url, signature}}.
  merge <version> <out_file> <fragment_file...>
      Merge fragment files into a full latest.json.
"""
import sys
import json
import datetime


def fragment() -> None:
    key, url, sig_file, out_file = sys.argv[2:6]
    sig = open(sig_file, encoding="utf-8").read().strip()
    with open(out_file, "w", encoding="utf-8") as fh:
        json.dump({key: {"url": url, "signature": sig}}, fh)
    print(f"wrote fragment {key} -> {out_file}")


def merge() -> None:
    version, out_file = sys.argv[2], sys.argv[3]
    platforms = {}
    for path in sys.argv[4:]:
        with open(path, encoding="utf-8") as fh:
            platforms.update(json.load(fh))
    latest = {
        "version": version,
        "notes": f"DeepSeek Harness desktop {version}",
        "pub_date": datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "platforms": platforms,
    }
    with open(out_file, "w", encoding="utf-8") as fh:
        json.dump(latest, fh, indent=2)
    print(f"wrote latest.json -> {out_file}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "fragment":
        fragment()
    elif cmd == "merge":
        merge()
    else:
        raise SystemExit(
            f"usage: updater-manifest.py fragment|merge ... (got {cmd!r})"
        )
