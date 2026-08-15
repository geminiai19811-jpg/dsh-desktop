#!/usr/bin/env python3
"""Upload update artifacts + a `latest.json` (with OSS URLs) to Aliyun OSS.

Used by the release workflow. Reads the per-platform signature fragments
(`dist-assets/latest-<platform>.json`, produced by the build jobs) so the
signatures stay byte-identical to the GitHub `latest.json`; only the download
URLs are rewritten to point at OSS.

Env vars (GitHub secrets):
  OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET, OSS_BUCKET, OSS_REGION
"""
import os
import sys
import json
import datetime

import oss2

# platform key -> local installer filename that the updater downloads.
UPLOADS = {
    "darwin-aarch64": "DeepSeek.Harness_{version}_aarch64.app.tar.gz",
    "windows-x86_64": "DeepSeek.Harness_{version}_x64-setup.exe",
}


def main() -> None:
    version = sys.argv[1]
    dist_dir = sys.argv[2]

    key_id = os.environ["OSS_ACCESS_KEY_ID"]
    key_secret = os.environ["OSS_ACCESS_KEY_SECRET"]
    bucket_name = os.environ["OSS_BUCKET"]
    region = os.environ["OSS_REGION"]

    auth = oss2.Auth(key_id, key_secret)
    bucket = oss2.Bucket(auth, f"https://{region}.aliyuncs.com", bucket_name)

    platforms = {}
    for platform_key, filename_tpl in UPLOADS.items():
        filename = filename_tpl.format(version=version)
        local = os.path.join(dist_dir, filename)
        if not os.path.exists(local):
            print(f"skip (missing): {filename}")
            continue

        key = f"{version}/{filename}"
        bucket.put_object_from_file(key, local)
        print(f"uploaded: {key}")

        # Signature comes from the fragment (URL-independent).
        frag_path = os.path.join(dist_dir, f"latest-{platform_key}.json")
        with open(frag_path, encoding="utf-8") as fh:
            signature = json.load(fh)[platform_key]["signature"]

        platforms[platform_key] = {
            "url": f"https://{bucket_name}.{region}.aliyuncs.com/{version}/{filename}",
            "signature": signature,
        }

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
