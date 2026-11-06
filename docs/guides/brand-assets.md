# Human guide — approved project artwork

Companion: [AI reference](../ai/brand-assets.md).
Software scope: JTS Tariff Engine v1.2.0; artwork source: JTS Brand System v1.1.0 commit.

Use the [asset gallery](../../assets/brand/README.md) to choose a logo. The square
Tariff Engine icon is the product mark; the tunnel is the JTS publisher mark.
Choose white transparent text on dark surfaces and Deep Space #071521 transparent
text on light surfaces. The opaque full variant has Deep Space background.
The company icon also comes in 800 x 800 at 504533 bytes, below 1 MB.

Keep all geometry, colors, text and aspect ratios. For a new render or edit use
the central Blender source set, never independently redraw these PNGs. Then
record the approved central commit and new checksums before copying exports.
The exact current source and SHA256 values are in the
[manifest](../../assets/brand/manifest.json). Access to private source requires
repository permission; displaying these local PNGs does not.

Verification: all nine PNGs match the central bytes, dimensions and hashes.
Inspect the correct white/dark variant on its intended background. The owner
approved the shown images and assigned Tariff artwork to this repository.
If an export changes unexpectedly, recover the recorded file from that commit.

Home Assistant uses a 256 × 256 downsample of the approved Tariff Engine
icon. The README keeps the company lockup and product icon distinct.

## Brand checks

Run `python tools/validate_brand.py` from the repository. GitHub Actions runs
the same check on every push and pull request. It verifies the README hierarchy,
paired product manuals, gallery previews and the approved image checksums against
the pinned JTS Brand System v1.1.0 source. When adopting a newly approved export,
update the manifest and checksum pins together in the same reviewed change.

Review rendered light/dark themes, mobile layout and accessibility manually.
The automated check uses project-local files and requires no private repository
access.
