"""Shared, compact read-only views of the precomputed quarter-hour schedule."""

import json
from datetime import timedelta
from zoneinfo import ZoneInfo

from homeassistant.util import dt as dt_util

from .api import PriceAPI, Status
from .price_engine import day_bounds


def quarter(now, offset=0):
    first = now.replace(minute=now.minute // 15 * 15, second=0, microsecond=0) + timedelta(
        minutes=15 * offset
    )
    return first, first + timedelta(minutes=15)


def report(c, day):
    return c.schedule.days.get(c.site["id"], {}).get(str(day), {})


def price(c, offset=0, now=None):
    return PriceAPI(c.hass).lookup(c.site["id"], *quarter(now or dt_util.utcnow(), offset), now=now)


def statistics(c, now=None, *, including_vat=True):
    """No Recorder samples or invented past rates; average exact schedule slots."""
    now = now or dt_util.utcnow()
    first, last = day_bounds(
        now.astimezone(ZoneInfo(c.site["timezone"])).date(), c.site["timezone"]
    )
    api = PriceAPI(c.hass)
    full = api.lookup(c.site["id"], first, last, now=now)
    selected, scope = full, "full_day"
    if full.status != Status.READY:
        candidates = [
            r.start
            for r in c.price_engine.lookup(c.site["id"], quarter(now)[0], last)
            if r.start >= quarter(now)[0]
        ]
        selected = None
        if candidates:
            remaining = api.lookup(c.site["id"], candidates[0], last, now=now)
            if remaining.status == Status.READY:
                selected, scope = remaining, "remaining_day"
    facts = {
        "scope": scope if selected and selected.status == Status.READY else "unavailable",
        "used_slots": 0,
        "day_slots": full.expected_slots,
        "reason": full.reason,
        "start": None,
        "end": last.isoformat(),
    }
    if selected and selected.status == Status.READY:
        values = [q.price for q in selected.slots]
        if not including_vat:
            records = {
                r.start: r
                for r in c.price_engine.lookup(c.site["id"], selected.slots[0].start, last)
            }
            values = [display_price(records[q.start], "ex_vat") for q in selected.slots]
        facts.update(
            used_slots=len(values),
            start=selected.slots[0].start.isoformat(),
            average=sum(values) / len(values),
            minimum=min(values),
            maximum=max(values),
            reason=None,
        )
    return facts


def display_basis(c):
    return "incl_vat" if c.site.get("display_including_vat", True) else "ex_vat"


def display_price(record, basis):
    """Project full-precision stored components; canonical prices never change."""
    if basis == "incl_vat":
        return record.final_price_incl_vat
    return sum(p["ex_vat"] for p in json.loads(record.components_json)["components"].values())


def breakdown(c, now=None):
    now = now or dt_util.utcnow()
    basis = display_basis(c)
    for offset, label in ((0, "current_quarter"), (1, "next_quarter")):
        window = price(c, offset, now)
        if window.status != Status.READY:
            continue
        row = c.price_engine.lookup(c.site["id"], *quarter(now, offset))[0]
        parts = json.loads(row.components_json)["components"]
        return {
            "period": label,
            "start": row.start.isoformat(),
            "end": row.end.isoformat(),
            "unit": "øre/kWh",
            "revision": row.revision,
            "source": json.loads(row.source_json),
            "component_basis": basis,
            "final_basis": basis,
            "components": {k: {**p, "value_ore": p[basis] * 100} for k, p in parts.items()},
            "vat_amount_ore": sum(p["vat"] for p in parts.values()) * 100,
            "final_ore": display_price(row, basis) * 100,
        }
    day = now.astimezone(ZoneInfo(c.site["timezone"])).date()
    state = report(c, day)
    return {
        "period": "unavailable",
        "components": {},
        "component_basis": basis,
        "final_basis": basis,
        "reason": state.get("reason") or window.reason,
        "missing_components": state.get("missing_components", []),
        "failure_stage": state.get("failure_stage"),
        "action": state.get("required_action"),
    }


def source_value(c, kind, now=None):
    now = now or dt_util.utcnow()
    first, last = quarter(now, int(kind == "next_spot"))
    day = first.astimezone(ZoneInfo(c.site["timezone"])).date()
    raw = report(c, day).get("raw", {})
    try:
        stamp = dt_util.parse_datetime(raw.get("verified_at", ""))
        fresh = stamp and 0 <= (now - stamp).total_seconds() <= 86400
    except TypeError, ValueError:
        fresh = False
    if kind in {"current_spot", "next_spot"}:
        if not fresh or raw.get("status") not in {"READY", "INCOMPLETE"}:
            return None
        return next(
            (
                s.price
                for s in c.price_updater.raw_slots.get(str(day), ())
                if s.start == first and s.end == last
            ),
            None,
        )
    if report(c, day).get("failure_stage") in {"source", "grid"}:
        return None
    part = c.price_updater.grid_slots.get(str(day), {}).get(first)
    return part["ex_vat"] if part else None


def availability(c, now=None):
    now = now or dt_util.utcnow()
    day = now.astimezone(ZoneInfo(c.site["timezone"])).date()
    current, following = price(c, 0, now), price(c, 1, now)
    tomorrow = PriceAPI(c.hass).lookup(
        c.site["id"], *day_bounds(day + timedelta(days=1), c.site["timezone"]), now=now
    )
    r = report(c, day)
    code = (
        "ready"
        if current.status == Status.READY
        else "error"
        if current.status == Status.ERROR
        else "stale"
        if current.status == Status.STALE
        else "waiting"
        if following.status == Status.READY
        else "missing"
    )
    facts = {
        "code": code,
        "current_status": str(current.status),
        "next_status": str(following.status),
        "tomorrow_status": str(tomorrow.status),
        "current_slots": current.available_slots,
        "next_slots": following.available_slots,
        "tomorrow_slots": tomorrow.available_slots,
        "tomorrow_expected": tomorrow.expected_slots,
        "available_from": following.slots[0]
        .start.astimezone(ZoneInfo(c.site["timezone"]))
        .isoformat(timespec="minutes")
        if following.status == Status.READY
        else None,
        "reason": current.reason or r.get("reason"),
        "action": r.get("required_action"),
        "affected_period": r.get("affected_period"),
        "missing_components": r.get("missing_components", []),
        "statistics": statistics(c, now),
        "breakdown": breakdown(c, now),
        "next_check": c.schedule.next_update(now).isoformat(),
    }
    return facts


def local_interval(start, end, timezone):
    """Readable local clock range; exact dated/offset identities remain available."""
    first, last = start.astimezone(ZoneInfo(timezone)), end.astimezone(ZoneInfo(timezone))
    finish = (
        "24:00"
        if last.date() > first.date() and last.hour == last.minute == 0
        else last.strftime("%H:%M")
    )
    # A repeated DST hour can have identical local clocks but distinct UTC identities.
    begin = first.strftime("%H:%M")
    if first.date() == last.date() and last.replace(tzinfo=None) <= first.replace(tzinfo=None):
        begin += first.strftime("%z")
        finish += last.strftime("%z")
    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "local_start": first.isoformat(timespec="minutes"),
        "local_end": last.isoformat(timespec="minutes"),
        "time_range": begin + "–" + finish,
    }


def grid_periods(c, now=None):
    """Today's actual contiguous grid bands, independent of final-price coverage.

    Only inspect the prepared update-time cache. Never normalize tariffs, fetch a
    source or calculate a final price here. Distinct nonadjacent equal rates and
    explicitly configured local-hour bands retain separate rows.
    """
    now = now or dt_util.utcnow()
    today = now.astimezone(ZoneInfo(c.site["timezone"])).date()
    metadata = c.price_updater.grid_sources.get(str(today), {})
    stamp = dt_util.parse_datetime(metadata.get("verified_at") or "")
    if not stamp or stamp.tzinfo is None or not 0 <= (now - stamp).total_seconds() <= 86400:
        return []
    if report(c, today).get("failure_stage") == "grid":
        return []
    grid = c.price_updater.grid_slots.get(str(today), {})
    if not grid:
        return []
    first, last = day_bounds(today, c.site["timezone"])
    periods, previous_band = [], None
    while first < last:
        end = first + timedelta(minutes=15)
        part = grid.get(first)
        evidence = {
            "value": part[display_basis(c)] * 100 if part else None,
            "value_basis": display_basis(c),
            **({k: part[k] for k in ("ex_vat", "vat", "incl_vat")} if part else {}),
            "status": "READY" if part else "INCOMPLETE",
            "source": part.get("source") if part else None,
            "verified_on": part.get("verified_on") if part else None,
            "verified_at": metadata.get("fetched_at"),
            "valid_from": part.get("valid_from") if part else None,
            "valid_to": part.get("valid_to") if part else None,
        }
        band = (
            evidence,
            part.get("hours") if part else None,
            part.get("effective_after") if part else None,
        )
        if periods and band == previous_band:
            periods[-1].update(
                end=end.isoformat(),
                local_end=end.astimezone(ZoneInfo(c.site["timezone"])).isoformat(
                    timespec="minutes"
                ),
            )
        else:
            periods.append(
                {
                    **{
                        k: v
                        for k, v in local_interval(first, end, c.site["timezone"]).items()
                        if k != "time_range"
                    },
                    **evidence,
                }
            )
        previous_band = band
        first = end
    return periods
