"""Primary prices plus the complete native diagnostic calculation and grid bands."""

from zoneinfo import ZoneInfo

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.event import async_track_utc_time_change
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .status import (
    availability,
    breakdown,
    display_basis,
    grid_periods,
    local_interval,
    price,
    source_value,
    statistics,
)

KINDS = (
    "current_spot",
    "current_final",
    "next_spot",
    "next_final",
    "average",
    "minimum",
    "maximum",
    "dso",
    "availability",
)


COMPONENT_KINDS = (
    "spot",
    "dso",
    "energinet_net",
    "energinet_system",
    "supplier",
    "electricity_tax",
    "vat",
    "final",
)


async def async_setup_entry(hass, entry, async_add_entities):
    c = entry.runtime_data
    async_add_entities(
        [PriceSensor(c, kind) for kind in KINDS]
        + [DiagnosticSensor(c, "price_period"), DiagnosticSensor(c, "including_vat")]
        + [DiagnosticSensor(c, "component_" + kind) for kind in COMPONENT_KINDS]
    )
    count = 0

    @callback
    def add_periods():
        nonlocal count
        needed = max(4, len(grid_periods(c)))
        if needed > count:
            async_add_entities(
                [DiagnosticSensor(c, "grid_period_" + str(i + 1), i) for i in range(count, needed)]
            )
            count = needed

    add_periods()
    entry.async_on_unload(c.async_add_listener(add_periods))


class PriceSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, kind):
        super().__init__(coordinator)
        self.kind = kind
        self._attr_unique_id = f"{coordinator.site['id']}_{kind}"
        self._attr_translation_key = kind
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.site["id"])},
            name=coordinator.site["name"],
            manufacturer="Energy Price Engine",
            model="Electricity pricing",
            entry_type=DeviceEntryType.SERVICE,
            sw_version=coordinator.integration_version,
        )
        if kind == "availability":
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        else:
            self._attr_native_unit_of_measurement = "øre/kWh"
            self._attr_suggested_display_precision = 2
            if kind in {"current_spot", "current_final", "dso"}:
                self._attr_state_class = SensorStateClass.MEASUREMENT

    async def async_added_to_hass(self):
        await super().async_added_to_hass()

        @callback
        def tick(_):
            self.async_write_ha_state()

        self.async_on_remove(async_track_utc_time_change(self.hass, tick, minute="*", second=0))

    @property
    def name(self):
        if (
            self.kind in {"average", "minimum", "maximum"}
            and statistics(self.coordinator)["scope"] == "remaining_day"
        ):
            da = self.coordinator.hass.config.language.startswith("da")
            return (
                {
                    "average": "Gennemsnit resten af dagen (inkl. moms)",
                    "minimum": "Minimum resten af dagen (inkl. moms)",
                    "maximum": "Maksimum resten af dagen (inkl. moms)",
                }
                if da
                else {
                    "average": "Remaining-day average (incl VAT)",
                    "minimum": "Remaining-day minimum (incl VAT)",
                    "maximum": "Remaining-day maximum (incl VAT)",
                }
            )[self.kind]
        return super().name

    @property
    def native_value(self):
        if self.kind == "availability":
            facts = availability(self.coordinator)
            da = self.coordinator.hass.config.language.startswith("da")
            words = (
                {
                    "ready": "Klar",
                    "error": "Fejl — se årsag og afhjælpning",
                    "stale": "Forældet — kontroller kilden",
                    "waiting": "Priser fra {time}",
                    "missing": "Manglende priser — se kilde/tarif",
                }
                if da
                else {
                    "ready": "Ready",
                    "error": "Error — see reason and action",
                    "stale": "Stale — recheck source",
                    "waiting": "Prices available from {time}",
                    "missing": "Missing prices — inspect source/tariff",
                }
            )
            return words[facts["code"]].format(time=facts["available_from"] or "—")
        if self.kind in {"average", "minimum", "maximum"}:
            value = statistics(self.coordinator).get(self.kind)
        elif self.kind in {"current_final", "next_final"}:
            result = price(self.coordinator, int(self.kind == "next_final"))
            value = result.slots[0].price if result.slots else None
        else:
            value = source_value(self.coordinator, self.kind)
        return value * 100 if value is not None else None

    @property
    def extra_state_attributes(self):
        if self.kind == "availability":
            return {"site_id": self.coordinator.site["id"], **availability(self.coordinator)}
        if self.kind in {"average", "minimum", "maximum"}:
            return {**statistics(self.coordinator), "vat_included": True, "value_basis": "incl_vat"}
        return {
            "site_id": self.coordinator.site["id"],
            "vat_included": self.kind.endswith("final"),
            "value_basis": "incl_vat" if self.kind.endswith("final") else "ex_vat",
            "canonical_unit": "DKK/kWh",
        }


class DiagnosticSensor(PriceSensor):
    """Numbers from ONE stored record; day grid bands use their own verified cache."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = None

    def __init__(self, coordinator, kind, index=None):
        super().__init__(coordinator, kind)
        self.index = index
        if kind in {"price_period", "including_vat"}:
            self._attr_native_unit_of_measurement = None
            self._attr_suggested_display_precision = None
            if kind == "including_vat":
                self._attr_device_class = SensorDeviceClass.ENUM
                self._attr_options = ["yes", "no"]
        elif index is not None:
            self._attr_translation_key = "grid_period"

    def _period(self):
        rows = grid_periods(self.coordinator)
        return rows[self.index] if self.index < len(rows) else None, rows

    @property
    def name(self):
        c = self.coordinator
        da = c.hass.config.language.startswith("da")
        if self.index is not None:
            row, _ = self._period()
            label = "Radius" if c.site["dso_mode"] == "radius_c" else "Net" if da else "DSO"
            time = (
                local_interval(
                    dt_util.parse_datetime(row["start"]),
                    dt_util.parse_datetime(row["end"]),
                    c.site["timezone"],
                )["time_range"]
                if row
                else ("utilgængelig" if da else "unavailable")
            )
            return f"{label} {self.index + 1} · {time}"
        if self.kind == "price_period":
            part = breakdown(c)
            if part["period"] == "current_quarter":
                return "Aktuelt kvarter" if da else "Current quarter"
            if part["period"] == "next_quarter":
                return "Næste verificerede kvarter" if da else "Next verified quarter"
        return super().name

    @property
    def native_value(self):
        c = self.coordinator
        if self.kind == "including_vat":
            return "yes" if c.site.get("display_including_vat", True) else "no"
        if self.index is not None:
            row, _ = self._period()
            return row["value"] if row else None
        data = breakdown(c)
        if self.kind == "price_period":
            if data["period"] == "unavailable":
                da = c.hass.config.language.startswith("da")
                if missing := data["missing_components"]:
                    names = {
                        "supplier": ("supplier markup", "leverandørtillæg"),
                        "dso": ("DSO tariff", "nettarif"),
                        "energinet_net": ("Energinet network", "Energinet net"),
                        "energinet_system": ("Energinet system", "Energinet system"),
                        "electricity_tax": ("electricity tax", "elafgift"),
                    }
                    return ("Manglende: " if da else "Missing: ") + ", ".join(
                        names.get(key, (key, key))[int(da)] for key in missing
                    )
                if data.get("failure_stage") == "storage":
                    return (
                        "Lagerfejl — kontroller gendannelse"
                        if da
                        else "Storage error — check recovery"
                    )
                return (
                    "Kilde utilgængelig — kontroller priser"
                    if da
                    else "Source unavailable — Check prices"
                )
            first, last = dt_util.parse_datetime(data["start"]), dt_util.parse_datetime(data["end"])
            value = local_interval(first, last, c.site["timezone"])["time_range"]
            if (
                first.astimezone(ZoneInfo(c.site["timezone"])).date()
                != dt_util.now().astimezone(ZoneInfo(c.site["timezone"])).date()
            ):
                value = first.astimezone(ZoneInfo(c.site["timezone"])).strftime("%d/%m ") + value
            return value
        if data["period"] == "unavailable":
            return None
        component = self.kind.removeprefix("component_")
        if component == "vat":
            return data["vat_amount_ore"]
        if component == "final":
            return data["final_ore"]
        return data["components"].get(component, {}).get("value_ore")

    @property
    def extra_state_attributes(self):
        c = self.coordinator
        if self.kind == "including_vat":
            return {
                "site_id": c.site["id"],
                "scope": "diagnostics_and_dashboard",
                "primary_sensor_basis": "fixed; see each sensor label",
                "value_basis": display_basis(c),
            }
        if self.index is not None:
            row, rows = self._period()
            return {
                "site_id": c.site["id"],
                "vat_included": c.site.get("display_including_vat", True),
                "period_count": len(rows),
                "additional_periods": max(0, len(rows) - 4),
                "period_number": self.index + 1,
                **(
                    row
                    or {
                        "status": "INCOMPLETE",
                        "reason": "No verified grid range at this index; use Check prices if expected",
                    }
                ),
            }
        data = breakdown(c)
        return {
            "site_id": c.site["id"],
            **{k: v for k, v in data.items() if k != "components"},
            "vat_included": None
            if self.kind in {"price_period", "component_vat"}
            else c.site.get("display_including_vat", True),
            "value_basis": "vat_amount" if self.kind == "component_vat" else display_basis(c),
            "component": self.kind.removeprefix("component_"),
            "applied_component": data["components"].get(self.kind.removeprefix("component_")),
            "verification": "unavailable" if data["period"] == "unavailable" else "verified",
        }
