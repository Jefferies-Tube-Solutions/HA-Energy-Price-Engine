"""VAT projection uses canonical snapshots and never mutates pricing or Recorder basis."""

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from custom_components.ha_energy_price_engine.api import get_api
from custom_components.ha_energy_price_engine.configuration import settings, validate_site
from custom_components.ha_energy_price_engine.const import DOMAIN, PRICE_REVISION_EVENT
from custom_components.ha_energy_price_engine.dashboard import price_schedule
from custom_components.ha_energy_price_engine.sensor import COMPONENT_KINDS, KINDS
from custom_components.ha_energy_price_engine.status import grid_periods

from .helpers import model, rule
from .test_device_diagnostics import states
from .test_integration import setup


@pytest.mark.parametrize("invalid", ["false", "true", 0, 1, None, [], {}])
def test_display_option_requires_real_boolean(invalid):
    assert validate_site(model())["display_including_vat"] is True
    with pytest.raises(ValueError, match="boolean"):
        validate_site(model(display_including_vat=invalid))


@pytest.mark.parametrize("including", [True, False])
@pytest.mark.parametrize("offset", [0, 1])
async def test_same_quarter_mixed_vat_projection_and_unchanged_actual_tax(
    hass, freezer, price_service, including, offset
):
    freezer.move_to("2026-11-01T10:15:00Z")
    price_service["amount"] = -1000
    now = datetime.now(UTC)
    data = model(
        display_including_vat=including,
        dated_components=[
            rule(
                "supplier",
                3.75,
                vat_included=True,
                vat_rate=0.1,
                **(
                    {"effective_after": (now + timedelta(minutes=15)).isoformat()} if offset else {}
                ),
            ),
            rule("dso", 22, vat_included=True, vat_rate=0.1),
            rule("electricity_tax", 0.8, vat_rate=0),
        ],
    )
    entry = await setup(hass, data)
    c = entry.runtime_data
    first = now + timedelta(minutes=15 * offset)
    record = c.price_engine.lookup("home", first, first + timedelta(minutes=15))[0]
    parts = json.loads(record.components_json)["components"]
    basis = "incl_vat" if including else "ex_vat"
    values = states(hass, entry)
    assert values["including_vat"].state == ("yes" if including else "no")
    assert values["including_vat"].attributes["options"] == ["yes", "no"]
    for key, part in parts.items():
        assert float(values["component_" + key].state) == pytest.approx(part[basis] * 100)
    final = float(values["component_final"].state)
    assert final == pytest.approx(sum(p[basis] for p in parts.values()) * 100)
    assert float(values["component_vat"].state) == pytest.approx(
        sum(p["vat"] for p in parts.values()) * 100
    )
    assert float(values["component_spot"].state) < 0
    assert values["price_period"].attributes["period"] == (
        "next_quarter" if offset else "current_quarter"
    )
    assert all(
        values["component_" + k].attributes["revision"] == record.revision for k in COMPONENT_KINDS
    )
    assert grid_periods(c)[0]["value"] == pytest.approx(22 if including else 20)
    card = price_schedule(c)
    quarter = next(r for r in card["days"][0]["slots"] if r["start"] == first.isoformat())
    assert quarter["final"] == pytest.approx(final)
    assert quarter["raw_spot"] == pytest.approx(parts["spot"]["ex_vat"] * 100)
    assert card["component_basis"] == card["final_basis"] == basis
    assert card["raw_spot_basis"] == "ex_vat"
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_configure_persists_without_reload_fetch_write_revision_or_history_change(
    hass, freezer, price_service, radius_source
):
    freezer.move_to("2026-11-01T10:15:00Z")
    entry = await setup(hass, model(dso_mode="radius_c", dated_components=[rule("supplier", 3)]))
    c = entry.runtime_data
    assert "display_including_vat" not in entry.data  # Original beta.11 configuration.
    assert c.site["display_including_vat"] is True
    baseline = states(hass, entry)
    records = c.price_engine.records["home"]
    ledger_bytes = await hass.async_add_executor_job(c.price_engine.database.path.read_bytes)
    before = get_api(hass).lookup(
        "home", datetime.now(UTC), datetime.now(UTC) + timedelta(minutes=15)
    )
    calls = len(price_service["calls"])
    events = []
    unsub = hass.bus.async_listen(PRICE_REVISION_EVENT, events.append)
    for including in (False, True, False):
        result = await hass.config_entries.options.async_init(entry.entry_id)
        assert "display" in result["menu_options"]
        fid = result["flow_id"]
        result = await hass.config_entries.options.async_configure(fid, {"next_step_id": "display"})
        assert result["step_id"] == "display"
        with (
            patch.object(
                hass.config_entries, "async_reload", side_effect=AssertionError("display reload")
            ),
            patch.object(
                c.price_updater.official, "get", side_effect=AssertionError("display source fetch")
            ),
            patch.object(
                c.price_updater.tariffs, "get", side_effect=AssertionError("display tariff fetch")
            ),
            patch.object(
                c.price_engine.database,
                "async_commit",
                side_effect=AssertionError("display ledger write"),
            ),
            patch(
                "custom_components.ha_energy_price_engine.price_engine.calculate",
                side_effect=AssertionError("display reprice"),
            ),
        ):
            result = await hass.config_entries.options.async_configure(
                fid, {"display_including_vat": including}
            )
            assert result["step_id"] == "review"
            await hass.async_block_till_done()
            assert settings(entry)["display_including_vat"] is including
            assert entry.runtime_data is c and c.settings_current
            current = states(hass, entry)
            assert current["including_vat"].state == ("yes" if including else "no")
            assert float(current["component_vat"].state) == float(baseline["component_vat"].state)
            for kind in KINDS:
                if kind != "availability":
                    assert current[kind].state == baseline[kind].state
                    assert current[kind].attributes.get("state_class") == baseline[
                        kind
                    ].attributes.get("state_class")
                    assert "VAT" in current[kind].attributes["friendly_name"]
            assert c.price_engine.records["home"] == records
            assert (
                get_api(hass).lookup(
                    "home", datetime.now(UTC), datetime.now(UTC) + timedelta(minutes=15)
                )
                == before
            )
            assert (
                await hass.async_add_executor_job(c.price_engine.database.path.read_bytes)
            ) == ledger_bytes
            card = price_schedule(c)
            assert card["display_including_vat"] is including
            assert len(price_service["calls"]) == calls
        await hass.config_entries.options.async_configure(fid, {"next_step_id": "done"})
        await hass.async_block_till_done()
    assert events == []
    unsub()
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.runtime_data.site["display_including_vat"] is False
    assert states(hass, entry)["including_vat"].state == "no"
    assert (
        await hass.async_add_executor_job(entry.runtime_data.price_engine.database.path.read_bytes)
    ) == ledger_bytes
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_initial_setup_saves_no_and_interrupted_display_edit_keeps_choice(
    hass, freezer, price_service
):
    freezer.move_to("2026-11-01T10:15:00Z")
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    fields = {str(k): k for k in result["data_schema"].schema}
    assert fields["display_including_vat"].default() is True
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "name": "Saved No",
            "nordpool_entry": "np",
            "display_including_vat": False,
        },
    )
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert settings(entry)["display_including_vat"] is False
    hass.config_entries.flow.async_abort(result["flow_id"])
    await hass.async_block_till_done()
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_unsent_display_edit_and_site_form_preserve_no(hass, freezer, price_service):
    freezer.move_to("2026-11-01T10:15:00Z")
    entry = await setup(hass, model(display_including_vat=False))
    before = len(price_service["calls"])
    result = await hass.config_entries.options.async_init(entry.entry_id)
    fid = result["flow_id"]
    form = await hass.config_entries.options.async_configure(fid, {"next_step_id": "display"})
    key = next(k for k in form["data_schema"].schema if str(k) == "display_including_vat")
    assert key.default() is False
    hass.config_entries.options.async_abort(fid)
    assert settings(entry)["display_including_vat"] is False
    result = await hass.config_entries.options.async_init(entry.entry_id)
    fid = result["flow_id"]
    form = await hass.config_entries.options.async_configure(fid, {"next_step_id": "site"})
    key = next(k for k in form["data_schema"].schema if str(k) == "display_including_vat")
    assert key.default() is False
    await hass.config_entries.options.async_configure(
        fid,
        {
            "name": entry.title,
            "nordpool_entry": "np",
            "display_including_vat": False,
        },
    )
    hass.config_entries.options.async_abort(fid)
    assert len(price_service["calls"]) == before
    assert settings(entry)["display_including_vat"] is False
    assert await hass.config_entries.async_unload(entry.entry_id)


@pytest.mark.parametrize("instant", ["2026-03-29T10:15:00Z", "2026-10-25T10:15:00Z"])
async def test_no_mode_missing_final_keeps_verified_dst_bands(
    hass, freezer, price_service, radius_source, instant
):
    freezer.move_to(instant)
    entry = await setup(
        hass, model(display_including_vat=False, dso_mode="radius_c", dated_components=[])
    )
    c = entry.runtime_data
    values = states(hass, entry)
    assert values["including_vat"].state == "no"
    assert all(values["component_" + k].state == "unknown" for k in COMPONENT_KINDS)
    bands = grid_periods(c)
    assert len(bands) == 4
    for i, band in enumerate(bands, 1):
        assert float(values["grid_period_" + str(i)].state) == pytest.approx(band["ex_vat"] * 100)
        assert band["value_basis"] == "ex_vat"
    assert await hass.config_entries.async_unload(entry.entry_id)
