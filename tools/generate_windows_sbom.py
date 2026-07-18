"""Generate an SPDX 2.3 JSON inventory for an exact portable candidate."""

import argparse
import hashlib
import json
import re
import uuid
from pathlib import Path


LICENSES = {
    "altgraph": "MIT",
    "coverage": "Apache-2.0",
    "greenlet": "MIT AND PSF-2.0",
    "importlib-metadata": "Apache-2.0",
    "markdown": "BSD-3-Clause",
    "packaging": "Apache-2.0 OR BSD-2-Clause",
    "pefile": "MIT",
    "pillow": "MIT-CMU",
    "playwright": "Apache-2.0",
    "pyee": "MIT",
    "pyinstaller": "GPL-2.0-or-later WITH Bootloader-exception",
    "pyinstaller-hooks-contrib": "Apache-2.0",
    "pypdfium2": "BSD-3-Clause AND Apache-2.0",
    "pywin32-ctypes": "BSD-3-Clause",
    "ruff": "MIT",
    "setuptools": "MIT",
    "tkinterdnd2": "MIT",
    "typing-extensions": "PSF-2.0",
    "zipp": "MIT",
}


def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha1_file(path):
    return hashlib.sha1(path.read_bytes()).hexdigest()


def locked_packages(lock_path):
    """Parse exact requirement records and their archive hashes."""
    records = []
    current = ""
    for raw_line in lock_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        current += (" " if current else "") + line.rstrip("\\").strip()
        if line.endswith("\\"):
            continue
        match = re.match(r"^([A-Za-z0-9_.-]+)==([^\s]+)", current)
        if not match:
            raise ValueError("Unrecognized locked requirement: " + current)
        name = match.group(1)
        records.append({
            "hashes": re.findall(r"--hash=sha256:([0-9a-f]{64})", current),
            "license": LICENSES.get(name.lower().replace("_", "-"), "NOASSERTION"),
            "name": name,
            "version": match.group(2),
        })
        current = ""
    if current:
        raise ValueError("Incomplete requirement continuation")
    return records


def spdx_id(prefix, value):
    cleaned = re.sub(r"[^A-Za-z0-9.-]", "-", value)
    return "SPDXRef-{0}-{1}".format(prefix, cleaned)


def generate(lock_path, artifact_dir, commit, created):
    files = []
    for path in sorted(item for item in artifact_dir.rglob("*") if item.is_file()):
        relative = path.relative_to(artifact_dir).as_posix()
        digest = sha256_file(path)
        sha1_digest = sha1_file(path)
        files.append({
            "SPDXID": spdx_id("File", digest[:20]),
            "checksums": [
                {"algorithm": "SHA1", "checksumValue": sha1_digest},
                {"algorithm": "SHA256", "checksumValue": digest},
            ],
            "copyrightText": "NOASSERTION",
            "fileName": "./" + relative,
            "licenseConcluded": "NOASSERTION",
        })
    tree_payload = json.dumps(
        [(item["fileName"], item["checksums"][0]["checksumValue"]) for item in files],
        separators=(",", ":"),
    )
    tree_hash = hashlib.sha256(tree_payload.encode("utf-8")).hexdigest()
    root_id = "SPDXRef-Package-LibreMarkPDF"
    verification_code = hashlib.sha1(
        "".join(sorted(
            next(
                checksum["checksumValue"]
                for checksum in item["checksums"]
                if checksum["algorithm"] == "SHA1"
            )
            for item in files
        )).encode("ascii")
    ).hexdigest()
    packages = [{
        "SPDXID": root_id,
        "checksums": [{"algorithm": "SHA256", "checksumValue": tree_hash}],
        "copyrightText": "Copyright (c) 2026 LibreMark PDF contributors",
        "downloadLocation": "NOASSERTION",
        "filesAnalyzed": True,
        "licenseConcluded": "MIT",
        "licenseDeclared": "MIT",
        "name": "LibreMark PDF Windows portable candidate",
        "packageVerificationCode": {
            "packageVerificationCodeValue": verification_code
        },
        "supplier": "Organization: LibreMark PDF contributors",
        "versionInfo": commit,
    }]
    relationships = [{
        "spdxElementId": "SPDXRef-DOCUMENT",
        "relationshipType": "DESCRIBES",
        "relatedSpdxElement": root_id,
    }]
    for record in locked_packages(lock_path):
        package_id = spdx_id("Package", record["name"])
        package = {
            "SPDXID": package_id,
            "copyrightText": "NOASSERTION",
            "downloadLocation": "NOASSERTION",
            "externalRefs": [
                {
                    "referenceCategory": "PACKAGE-MANAGER",
                    "referenceLocator": "pkg:pypi/{0}@{1}".format(
                        record["name"], record["version"]
                    ),
                    "referenceType": "purl",
                }
            ],
            "filesAnalyzed": False,
            "licenseConcluded": record["license"],
            "licenseDeclared": record["license"],
            "name": record["name"],
            "versionInfo": record["version"],
        }
        if record["hashes"]:
            package["checksums"] = [
                {"algorithm": "SHA256", "checksumValue": value}
                for value in record["hashes"]
            ]
        packages.append(package)
        relationships.append({
            "spdxElementId": root_id,
            "relationshipType": "DEPENDS_ON",
            "relatedSpdxElement": package_id,
        })
    for item in files:
        relationships.append({
            "spdxElementId": root_id,
            "relationshipType": "CONTAINS",
            "relatedSpdxElement": item["SPDXID"],
        })
    namespace_uuid = uuid.uuid5(
        uuid.NAMESPACE_URL,
        "https://libremark.invalid/spdx/{0}/{1}".format(commit, tree_hash),
    )
    return {
        "SPDXID": "SPDXRef-DOCUMENT",
        "creationInfo": {
            "created": created,
            "creators": ["Tool: LibreMark-PDF-G3-SBOM-1"],
        },
        "dataLicense": "CC0-1.0",
        "documentNamespace": "https://libremark.invalid/spdx/" + str(namespace_uuid),
        "files": files,
        "name": "LibreMark-PDF-Windows-x64-" + commit[:12],
        "packages": packages,
        "relationships": relationships,
        "spdxVersion": "SPDX-2.3",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--created", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.artifact_dir.is_dir():
        parser.error("artifact directory is unavailable")
    document = generate(
        args.lock, args.artifact_dir, args.commit, args.created
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "files": len(document["files"]),
        "output": str(args.output),
        "packages": len(document["packages"]),
        "sha256": sha256_file(args.output),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
