# Older incompatible beta installations

Beta.12 → stable1.0.0 is an in-place update and needs no reset. Beta.10/11 share schema4.
This page applies only to older beta1–9 entries that intentionally fail schema migration.

Back up all Home Assistant configuration, `.storage`, Recorder and PE files first.
Record actual source mappings, supplier/grid rates, effective dates and overrides.
Install stable v1.0.0 through HACS, restart, and open an incompatible entry's Configure.
Its reset form requires the exact site name and explicit permanent-delete confirmation.
Only that selected entry and its PE files are removed. Recreate it with actual verified
settings. New IDs/entities/history are intentional for these older incompatible entries;
update any external mappings explicitly. Other sites and unrelated HA data are retained.

Normal HA Delete retains PE history. Explicit PE reset deletes it. Never use this older
procedure for a working beta.12 entry, bulk-delete PE files or edit `.storage` manually.
A complete stopped-HA backup restore is the supported rollback method.
