"""Actual HA diagnostic rows: coherent records, verified independent bands and no read I/O."""

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import EntityCategory
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.ha_energy_price_engine.configuration import current_rate
from custom_components.ha_energy_price_engine.dashboard import price_schedule
from custom_components.ha_energy_price_engine.sensor import COMPONENT_KINDS, KINDS, DiagnosticSensor
from custom_components.ha_energy_price_engine.status import breakdown, grid_periods

from .helpers import model, rule
from .test_integration import setup


def states(hass, entry):
    prefix = entry.runtime_data.site["id"] + "_"
    return {
        e.unique_id.removeprefix(prefix): hass.states.get(e.entity_id)
        for e in er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    }


def assert_record(values, row, scope):
    components = json.loads(row.components_json)["components"]
    expected = {k: part["incl_vat"] * 100 for k, part in components.items()}
    expected["vat"] = sum(part["vat"] for part in components.values()) * 100
    expected["final"] = row.final_price_incl_vat * 100
    for key in COMPONENT_KINDS:
        state = values["component_" + key]
        assert float(state.state) == pytest.approx(expected[key])
        assert state.attributes["unit_of_measurement"] == "øre/kWh"
        assert state.attributes["revision"] == row.revision
        assert state.attributes["start"] == row.start.isoformat()
        assert state.attributes["end"] == row.end.isoformat()
        assert state.attributes["period"] == scope
        assert state.attributes["verification"] == "verified"
        assert state.attributes["source"] == json.loads(row.source_json)
    assert sum(
        float(values["component_" + k].state) for k in COMPONENT_KINDS if k not in {"final", "vat"}
    ) == pytest.approx(expected["final"])


async def test_enabled_native_diagnostic_rows_current_record_and_no_read_io(
    hass, freezer, price_service, radius_source
):
    freezer.move_to("2026-11-01T10:15:00Z")
    entry = await setup(hass, model(dso_mode="radius_c", dated_components=[rule("supplier", 11.1)]))
    c = entry.runtime_data
    registry = er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    diagnostics = [e for e in registry if e.entity_category == EntityCategory.DIAGNOSTIC]
    assert len(registry) == 23 and len(diagnostics) == 15
    assert all(e.disabled_by is None for e in diagnostics)
    values = states(hass, entry)
    assert set(KINDS) <= values.keys()
    row = c.price_engine.lookup(
        "home", datetime(2026, 11, 1, 10, 15, tzinfo=UTC), datetime(2026, 11, 1, 10, 30, tzinfo=UTC)
    )[0]
    before = len(price_service["calls"])
    with (
        patch.object(
            c.price_updater.official, "get", side_effect=AssertionError("diagnostic source request")
        ),
        patch.object(
            c.price_updater.tariffs, "get", side_effect=AssertionError("diagnostic DSO request")
        ),
        patch.object(
            c.price_engine.database,
            "async_commit",
            side_effect=AssertionError("diagnostic DB write"),
        ),
        patch(
            "custom_components.ha_energy_price_engine.price_engine.calculate",
            side_effect=AssertionError("diagnostic final calculation"),
        ),
        patch(
            "custom_components.ha_energy_price_engine.price_components.compose_dated",
            side_effect=AssertionError("diagnostic tariff calculation"),
        ),
        patch(
            "custom_components.ha_energy_price_engine.tariff_source.normalize_tariffs",
            side_effect=AssertionError("diagnostic tariff normalization"),
        ),
    ):
        assert_record(values, row, "current_quarter")
        for key in COMPONENT_KINDS:
            sensor = DiagnosticSensor(c, "component_" + key)
            assert sensor.suggested_display_precision == 2
            assert sensor.entity_category == EntityCategory.DIAGNOSTIC
            assert sensor.state_class is None
            assert sensor.native_value == pytest.approx(float(values["component_" + key].state))
            assert sensor.extra_state_attributes["revision"] == row.revision
        assert DiagnosticSensor(c, "price_period").native_value == "11:15–11:30"
        assert len(grid_periods(c)) == 4
        assert len(price_schedule(c)["dso_today"]) == 4
    assert len(price_service["calls"]) == before
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_owner_shaped_next_quarter_example_then_automatic_switch(
    hass, freezer, price_service, radius_source
):
    # Explicit fictional supplier/source fixtures, NOT inferred owner's contract terms.
    freezer.move_to("2026-11-01T10:15:00Z")
    now = datetime.now(UTC)
    start = now + timedelta(minutes=15)

    def different_quarters(call, rows):
        for row in rows:
            row["price"] = 1746.836 if row["start"] == start.isoformat() else 1828
        return rows

    price_service["transform"] = different_quarters
    data = current_rate(
        model(dso_mode="radius_c", dated_components=[]),
        "supplier",
        "11.1",
        False,
        now + timedelta(seconds=1),
    )
    entry = await setup(hass, data)
    c = entry.runtime_data
    values = states(hass, entry)
    assert float(values["current_spot"].state) == 182.8
    assert float(values["dso"].state) == pytest.approx(31.8524)
    assert values["current_final"].state == "unknown"
    assert float(values["next_final"].state) == pytest.approx(287.42)
    assert "Next verified quarter" in values["price_period"].attributes["friendly_name"]
    assert values["price_period"].state == "11:30–11:45"
    row = c.price_engine.lookup("home", start, start + timedelta(minutes=15))[0]
    assert_record(values, row, "next_quarter")
    assert float(values["component_spot"].state) == pytest.approx(174.6836 * 1.25)
    assert float(values["component_spot"].state) != float(values["current_spot"].state)
    assert [values["grid_period_" + str(i)].state for i in range(1, 5)] != ["unknown"] * 4
    before = list(c.price_engine.records["home"])
    freezer.move_to(start)
    async_fire_time_changed(hass, start)
    await hass.async_block_till_done()
    after = states(hass, entry)
    assert "Current quarter" in after["price_period"].attributes["friendly_name"]
    assert_record(after, row, "current_quarter")
    assert c.price_engine.records["home"] == tuple(before)
    assert await hass.config_entries.async_unload(entry.entry_id)


@pytest.mark.parametrize(
    "instant,minimum_hours",
    [
        ("2026-03-29T10:15:00Z", 5),
        ("2026-04-02T10:15:00Z", 6),
        ("2026-10-25T10:15:00Z", 7),
        ("2026-11-01T10:15:00Z", 6),
    ],
)
async def test_day_grid_ranges_without_any_final_records_and_dst(
    hass, freezer, price_service, radius_source, instant, minimum_hours
):
    freezer.move_to(instant)
    entry = await setup(hass, model(dso_mode="radius_c", dated_components=[]))
    c = entry.runtime_data
    assert not c.price_engine.records.get("home")
    rows = grid_periods(c)
    assert len(rows) == 4
    assert [r["local_start"][11:16] for r in rows] == ["00:00", "06:00", "17:00", "21:00"]
    assert rows[1]["value"] == rows[3]["value"] and rows[1]["start"] != rows[3]["start"]
    assert (
        datetime.fromisoformat(rows[0]["end"]) - datetime.fromisoformat(rows[0]["start"])
    ).total_seconds() == minimum_hours * 3600
    values = states(hass, entry)
    assert "21:00–24:00" in values["grid_period_4"].attributes["friendly_name"]
    assert "Missing" in values["price_period"].state
    assert all(values["component_" + k].state == "unknown" for k in COMPONENT_KINDS)
    for i, row in enumerate(rows, 1):
        assert float(values["grid_period_" + str(i)].state) == pytest.approx(row["value"])
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_grid_verification_is_independent_but_stale_grid_never_invented(
    hass, freezer, price_service, radius_source
):
    freezer.move_to("2026-11-01T10:15:00Z")
    entry = await setup(hass, model(dso_mode="radius_c", dated_components=[]))
    c = entry.runtime_data
    previous = grid_periods(c)
    price_service["failure"] = True
    await c.schedule.refresh_day(c.site, datetime.now(UTC).date(), datetime.now(UTC))
    assert grid_periods(c) == previous
    assert breakdown(c)["period"] == "unavailable"
    c.schedule.days["home"]["2026-11-01"]["failure_stage"] = "grid"
    assert grid_periods(c) == []
    c.schedule.days["home"]["2026-11-01"]["failure_stage"] = "source"
    c.price_updater.grid_sources["2026-11-01"]["verified_at"] = "2026-10-30T10:15:00+00:00"
    assert grid_periods(c) == []
    assert all(
        DiagnosticSensor(c, "grid_period_" + str(i + 1), i).native_value is None for i in range(4)
    )
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_site_isolation_and_mixed_vat_negative_components(hass, freezer, price_service):
    freezer.move_to("2026-11-01T10:15:00Z")
    price_service["amount"] = -1000
    home = await setup(
        hass, model(dated_components=[rule("supplier", 3.75, vat_included=True), rule("dso", 20)])
    )
    away = await setup(
        hass,
        model(id="away", name="Away", dated_components=[rule("supplier", 11.1), rule("dso", 40)]),
    )
    for entry in (home, away):
        c = entry.runtime_data
        first = datetime.now(UTC)
        row = c.price_engine.lookup(c.site["id"], first, first + timedelta(minutes=15))[0]
        assert_record(states(hass, entry), row, "current_quarter")
    assert float(states(hass, home)["component_supplier"].state) == pytest.approx(3.75)
    assert float(states(hass, away)["component_supplier"].state) == pytest.approx(11.1 * 1.25)
    assert float(states(hass, home)["component_spot"].state) < 0
    assert await hass.config_entries.async_unload(home.entry_id)
    assert await hass.config_entries.async_unload(away.entry_id)


async def test_actual_ranges_not_hardcoded_and_additional_native_rows(hass, freezer, price_service):
    freezer.move_to("2026-11-01T10:15:00Z")
    rates = [
        rule("dso", 5, hours=[str(h) for h in range(7)]),
        rule("dso", 5, hours=["7", "8"]),
        rule("dso", 10, hours=["9", "10"]),
        rule("dso", 15, hours=["11", "12"]),
        rule("dso", 20, hours=[str(h) for h in range(13, 24)]),
    ]
    entry = await setup(hass, model(dated_components=[rule("supplier", 3), *rates]))
    c = entry.runtime_data
    rows = grid_periods(c)
    assert len(rows) == 5 and rows[0]["value"] == rows[1]["value"] == 6.25
    assert [r["local_start"][11:16] for r in rows] == ["00:00", "07:00", "09:00", "11:00", "13:00"]
    assert len(states(hass, entry)) == 24
    assert float(states(hass, entry)["grid_period_5"].state) == 25
    assert states(hass, entry)["grid_period_5"].attributes["additional_periods"] == 1
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_next_midnight_uses_tomorrow_record_not_todays_applied_tariff(
    hass, freezer, price_service, radius_source
):
    freezer.move_to("2026-11-01T22:45:00Z")
    now = datetime.now(UTC)
    data = current_rate(
        model(dso_mode="radius_c", dated_components=[]),
        "supplier",
        "11.1",
        False,
        now + timedelta(seconds=1),
    )
    entry = await setup(hass, data)
    c = entry.runtime_data
    values = states(hass, entry)
    assert values["price_period"].state == "02/11 00:00–00:15"
    assert values["component_dso"].attributes["period"] == "next_quarter"
    assert float(values["component_dso"].state) == pytest.approx(10.6175 * 1.25)
    assert float(values["dso"].state) == pytest.approx(31.8524)
    assert grid_periods(c)[-1]["local_start"].startswith("2026-11-01")
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_more_ranges_added_on_updates_then_unavailable_when_no_longer_applicable(
    hass, freezer, price_service, radius_source
):
    from copy import deepcopy
    from unittest.mock import AsyncMock

    from custom_components.ha_energy_price_engine.price_engine import day_bounds
    from custom_components.ha_energy_price_engine.tariff_source import (
        RADIUS_CODE,
        RADIUS_GLN,
        normalize_tariffs,
    )

    from .test_tariff_source import DATA

    freezer.move_to("2026-11-01T10:15:00Z")
    entry = await setup(hass, model(dso_mode="radius_c", dated_components=[rule("supplier", 3)]))
    c = entry.runtime_data
    assert len(states(hass, entry)) == 23
    records = deepcopy(DATA)
    for record in records:
        record["Price4"] = 0.2
    first, last = day_bounds(datetime.now(UTC).date())
    slots, meta = normalize_tariffs(records, RADIUS_GLN, RADIUS_CODE, first, last)
    with patch.object(
        c.price_updater.tariffs,
        "get",
        AsyncMock(return_value=(slots, {**meta, "fetched_at": datetime.now(UTC).isoformat()})),
    ):
        await c.schedule.refresh_day(c.site, datetime.now(UTC).date(), datetime.now(UTC))
        await c.async_refresh()
        await hass.async_block_till_done()
    assert len(grid_periods(c)) == 6
    assert len(states(hass, entry)) == 25
    assert float(states(hass, entry)["grid_period_6"].state) == pytest.approx(31.8524 * 1.25)
    await c.schedule.refresh_day(c.site, datetime.now(UTC).date(), datetime.now(UTC))
    await c.async_refresh()
    await hass.async_block_till_done()
    assert len(grid_periods(c)) == 4
    assert states(hass, entry)["grid_period_6"].state == "unknown"
    assert states(hass, entry)["grid_period_6"].attributes["period_count"] == 4
    assert await hass.config_entries.async_unload(entry.entry_id)
