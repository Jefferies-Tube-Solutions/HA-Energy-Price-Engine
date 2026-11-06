# AI reference — approved project artwork

Companion: [Human guide](../guides/brand-assets.md).
Software scope: JTS Tariff Engine v1.2.0; artwork source: JTS Brand System v1.1.0 source commit.

The authoritative consumer contract is [manifest.json](../../assets/brand/manifest.json).
Keys: schema_version (1), source_repository (owner/repo string), source_commit
(40-character Git SHA), source_version (1.1.0), source_status, approved_date and
files[]. Each file has path, source_path, sha256, bytes, width and height.

Company: `assets/brand/jts/v4/` contains five PNGs. Tariff product:
`assets/brand/tariff-engine/v1/` contains four PNGs. All are exact copies; native
Blender/Python/fonts remain central. Runtime `brand/icon.png` is a 256 × 256 downsample of the approved product icon.

README selects company white text with `#gh-dark-mode-only` and Deep Space
text with `#gh-light-mode-only`. Do not embed private raw URLs or tokens.
Deep Space is #071521, transparency uses alpha, and the cyan rule stays cyan.
Company text: JEFFERIES TUBE / SOLUTIONS / THE SYSTEMS BEHIND THE SYSTEMS.
Geometry and font metrics are locked in central Tunnel 06 / Layout 02.
Tariff identity is Symbol 04, warm euro/cyan bolt. Its full PNG preserves legacy
raster typography; its Blender file alone cannot yet reproduce that exact text.

Verification uses central registered checksums/dimensions/alpha validation and
byte-identical copies. The 800 company icon must be exactly 800x800 and smaller
than 1000000 bytes. Keep the Home Assistant domain, package and API identifiers
stable. Recover from the pinned source commit on hash mismatch.
