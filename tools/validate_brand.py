"""Check the Tariff Engine's pinned JTS Brand System rules (VIS-001–003, DOC-001)."""

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "Jefferies-Tube-Solutions/jts-tariff-engine"
BRAND = ROOT / "assets/brand"
COMPONENT = ROOT / "custom_components/ha_energy_price_engine"
# Approved JTS Brand System v1.1.0 source: 1f361188cfa1636a6cee81c20cff433787e6de23.
MANIFEST_SHA256 = "1c12ef0cd05eee879718656d4d131eb5703223c157c3ec1fe069d449908eb9e5"
RUNTIME_ICON_SHA256 = "27afd79349dba0ccd792ba57aff27ce5a559908ddadba209ea9550a9e61174f2"
HEADER_IMAGES = (
    "assets/brand/jts/v4/jts-white-transparent.png#gh-dark-mode-only",
    "assets/brand/jts/v4/jts-deep-space-transparent.png#gh-light-mode-only",
    "assets/brand/tariff-engine/v1/JTS_Tariff_Engine_Icon.png",
)
SECTIONS = (
    "Mission Directive",
    "System Registry",
    "Commissioning",
    "Operational Protocol",
    "Verification",
    "Fault Isolation and Recovery",
    "Manuals",
    "Operations Log",
)


def require(condition, message):
    if not condition:
        raise SystemExit(f"JTS brand check failed: {message}")


def check_readme(version, name):
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    title = f"# {name}\n"
    require(readme.count(title) == 1, f"README needs the title {title.strip()}")
    header = readme.split(title, 1)[0]
    badge = f"https://img.shields.io/github/v/release/{REPOSITORY}?label=stable&amp;color=2ea44f"
    latest = f"https://github.com/{REPOSITORY}/releases/latest"
    groups = re.findall(r'<p align="(right|center)">(.*?)</p>', header, re.DOTALL)
    require(
        header.startswith('<p align="right">')
        and [align for align, _ in groups] == ["right", "center", "center"],
        "use the right-aligned badge, centered publisher lockup and centered product icon",
    )
    expected = ((badge,), HEADER_IMAGES[:2], HEADER_IMAGES[2:])
    for (_, block), sources in zip(groups, expected, strict=True):
        images = re.findall(r"<img\b[^>]*>", block)
        require(
            tuple(re.findall(r'src="([^"]+)"', "".join(images))) == sources
            and len(images) == len(sources)
            and all(re.search(r'alt="[^"]+"', image) for image in images),
            f"incorrect image order, source or alt text in README header: {sources}",
        )
    require(f'href="{latest}"' in groups[0][1], "badge must link to the latest release")
    headings = re.findall(r"^## (.+)$", readme, re.MULTILINE)
    require(
        tuple(heading for heading in headings if heading in SECTIONS) == SECTIONS,
        "README sections must follow the JTS product documentation order",
    )

    for folder, counterpart in (("guides", "ai"), ("ai", "guides")):
        manual = f"docs/{folder}/tariff-engine.md"
        require(f"]({manual})" in readme, f"README is missing its link to {manual}")
        body = (ROOT / manual).read_text(encoding="utf-8")
        require(
            body.startswith(f"# {name} ")
            and re.search(rf"\bv{re.escape(version)}\b", body)
            and f"](../{counterpart}/tariff-engine.md)" in body,
            f"{manual} must match the product version and link to its counterpart",
        )


def check_assets():
    manifest = json.loads((BRAND / "manifest.json").read_text(encoding="utf-8"))
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    require(
        hashlib.sha256(canonical).hexdigest() == MANIFEST_SHA256,
        "the approved asset manifest changed; review the new JTS source before updating the pin",
    )
    gallery = (BRAND / "README.md").read_text(encoding="utf-8")
    require("| Preview |" in gallery, "the artwork gallery needs a Preview column")
    for entry in manifest["files"]:
        path = ROOT / entry["path"]
        require(
            hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"],
            f"{entry['path']} differs from the approved export",
        )
        relative = path.relative_to(BRAND).as_posix()
        require(
            re.search(rf'<img\b[^>]*src="{re.escape(relative)}"[^>]*alt="[^"]+"', gallery),
            f"gallery is missing an accessible preview for {relative}",
        )
    icon = COMPONENT / "brand/icon.png"
    require(
        hashlib.sha256(icon.read_bytes()).hexdigest() == RUNTIME_ICON_SHA256,
        "Home Assistant icon differs from the approved Tariff Engine downsample",
    )


def main():
    integration = json.loads((COMPONENT / "manifest.json").read_text(encoding="utf-8"))
    hacs = json.loads((ROOT / "hacs.json").read_text(encoding="utf-8"))
    require(
        integration["name"] == hacs["name"] == "JTS Tariff Engine",
        "Home Assistant and HACS must use the approved product name",
    )
    check_readme(integration["version"], integration["name"])
    check_assets()
    print("JTS brand check passed: README, product manuals, gallery and approved artwork")


if __name__ == "__main__":
    main()
