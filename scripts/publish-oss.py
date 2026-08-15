#!/usr/bin/env python3
"""Upload update artifacts + a `latest.json` (with OSS URLs) to Aliyun OSS.

Used by the release workflow. Reads the per-platform signature fragments
(`dist-assets/latest-<platform>.json`, produced by the build jobs) so the
signatures stay byte-identical to the GitHub `latest.json`; only the download
URLs are rewritten to point at OSS.

Also mirrors the manual installers (`.dmg`, `.app.zip`, `.msi`) so the website's
download buttons can serve fast downloads to users in China.

Env vars (GitHub secrets):
  OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET, OSS_BUCKET, OSS_REGION
"""
import os
import sys
import json
import datetime

import oss2

# platform key -> local installer filename that the updater downloads.
UPDATER_FILES = {
    "darwin-aarch64": "DeepSeek.Harness_{version}_aarch64.app.tar.gz",
    "windows-x86_64": "DeepSeek.Harness_{version}_x64-setup.exe",
}

# Manual installers mirrored for the website's download buttons.
MANUAL_FILES = {
    "DeepSeek.Harness_{version}_aarch64.dmg": "application/octet-stream",
    "DeepSeek.Harness_{version}_arm64.app.zip": "application/zip",
    "DeepSeek.Harness_{version}_x64_en-US.msi": "application/octet-stream",
}


def upload_file(bucket, local_path, key, content_type=None):
    headers = {"Content-Type": content_type} if content_type else {}
    bucket.put_object_from_file(key, local_path, headers=headers)
    print(f"uploaded: {key}")


def main() -> None:
    version = sys.argv[1]
    dist_dir = sys.argv[2]

    key_id = os.environ["OSS_ACCESS_KEY_ID"]
    key_secret = os.environ["OSS_ACCESS_KEY_SECRET"]
    bucket_name = os.environ["OSS_BUCKET"]
    region = os.environ["OSS_REGION"]

    auth = oss2.Auth(key_id, key_secret)
    bucket = oss2.Bucket(auth, f"https://{region}.aliyuncs.com", bucket_name)
    base = f"https://{bucket_name}.{region}.aliyuncs.com"

    platforms = {}
    for platform_key, filename_tpl in UPDATER_FILES.items():
        filename = filename_tpl.format(version=version)
        local = os.path.join(dist_dir, filename)
        if not os.path.exists(local):
            print(f"skip (missing): {filename}")
            continue

        upload_file(bucket, local, f"{version}/{filename}")

        # Signature comes from the fragment (URL-independent).
        frag_path = os.path.join(dist_dir, f"latest-{platform_key}.json")
        with open(frag_path, encoding="utf-8") as fh:
            signature = json.load(fh)[platform_key]["signature"]

        platforms[platform_key] = {
            "url": f"{base}/{version}/{filename}",
            "signature": signature,
        }

    # Mirror the manual installers (best-effort; skip any that are absent).
    for filename_tpl, content_type in MANUAL_FILES.items():
        filename = filename_tpl.format(version=version)
        local = os.path.join(dist_dir, filename)
        if not os.path.exists(local):
            print(f"skip (missing): {filename}")
            continue
        upload_file(bucket, local, f"{version}/{filename}", content_type)

    latest = {
        "version": version,
        "notes": f"DeepSeek Harness desktop {version}",
        "pub_date": datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "platforms": platforms,
    }

    # latest.json must not be cached, otherwise clients see stale versions.
    bucket.put_object(
        "latest.json",
        json.dumps(latest, indent=2),
        headers={"Content-Type": "application/json", "Cache-Control": "no-cache"},
    )
    print("uploaded: latest.json")
    print(json.dumps(latest, indent=2))


if __name__ == "__main__":
    main()
