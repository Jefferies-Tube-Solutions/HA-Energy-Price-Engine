"""Real native resource collections: cold load, adoption, restart and isolation."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.lovelace import LovelaceData
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.components.lovelace.dashboard import LovelaceStorage
from homeassistant.components.lovelace.resources import (
    ResourceStorageCollection,
    ResourceYAMLCollection,
)

from custom_components.ha_energy_price_engine.lovelace_resource import CARD_URL, async_register_card


def storage(hass, items, hass_storage):
    hass_storage["lovelace_resources"] = {
        "version": 1,
        "minor_version": 1,
        "data": {"items": items},
    }
    resources = ResourceStorageCollection(hass, LovelaceStorage(hass, None))
    assert not resources.loaded
    hass.data[LOVELACE_DATA] = LovelaceData("storage", {}, resources, {})
    return resources


@pytest.mark.parametrize(
    "existing",
    [
        None,
        CARD_URL,
        CARD_URL + "?v=1.0.0",
        CARD_URL + "?v=1.1.0-beta.1",
        CARD_URL + "?v=old#cache",
    ],
)
async def test_cold_start_adopts_manual_keeps_order_and_no_duplicates(hass, hass_storage, existing):
    unrelated = [
        {"id": "before", "url": "/local/another.js", "type": "module"},
        {"id": "prefix", "url": CARD_URL + ".other", "type": "module"},
        {"id": "external", "url": "https://example.org" + CARD_URL, "type": "module"},
    ]
    manual = [{"id": "manual", "url": existing, "type": "js"}] if existing else []
    original = unrelated[:1] + manual + unrelated[1:]
    resources = storage(hass, original, hass_storage)
    # No dashboard visit or resources WebSocket before PE setup.
    with patch(
        "custom_components.ha_energy_price_engine.lovelace_resource.async_get_integration",
        AsyncMock(return_value=SimpleNamespace(version="1.1.0")),
    ):
        await asyncio.gather(async_register_card(hass), async_register_card(hass))
        assert resources.loaded
        result = resources.async_items()
        ours = [i for i in result if i["url"].startswith(CARD_URL + "?")]
        assert len(ours) == 1 and ours[0]["type"] == "module"
        assert ours[0]["url"] == CARD_URL + "?v=1.1.0"
        assert [i for i in result if i not in ours] == unrelated
        if manual:
            assert result[1]["id"] == "manual"
        # Simulate fresh native collection after restart using its actual saved data.
        await resources.store.async_save(resources._data_to_save())
        restarted = ResourceStorageCollection(hass, LovelaceStorage(hass, None))
        hass.data[LOVELACE_DATA].resources = restarted
        await async_register_card(hass)
        assert restarted.async_items() == result
        with (
            patch.object(
                restarted, "async_update_item", side_effect=AssertionError("redundant update")
            ),
            patch.object(restarted, "async_create_item", side_effect=AssertionError("duplicate")),
        ):
            await async_register_card(hass)


async def test_yaml_resources_remain_user_owned(hass, caplog):
    items = [
        {"url": CARD_URL + "?v=1.0.0", "type": "module"},
        {"url": "/local/user.js", "type": "module"},
    ]
    resources = ResourceYAMLCollection(items.copy())
    hass.data[LOVELACE_DATA] = LovelaceData("yaml", {}, resources, {})
    with caplog.at_level("INFO"):
        await async_register_card(hass)
    assert resources.async_items() == items
    assert "YAML-managed" in caplog.text and "lovelace.resources" in caplog.text


async def test_ambiguous_duplicates_do_not_mutate_collection(hass, hass_storage, caplog):
    items = [
        {"id": "a", "url": CARD_URL, "type": "module"},
        {"id": "b", "url": CARD_URL + "?v=1.0.0", "type": "module"},
    ]
    resources = storage(hass, items, hass_storage)
    await async_register_card(hass)
    assert resources.async_items() == items
    assert "Keep one resource" in caplog.text and "a, b" in caplog.text


async def test_registration_failure_preserves_native_price_startup(
    hass, hass_storage, price_service, caplog
):
    from .test_integration import setup

    storage(hass, [], hass_storage)
    with patch.object(
        ResourceStorageCollection, "async_get_info", side_effect=OSError("read-only disk")
    ):
        entry = await setup(hass)
    assert entry.runtime_data.price_engine.records
    assert "read-only disk" in caplog.text and "Pricing continues" in caplog.text
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_multisite_unload_retains_single_global_resource(hass, price_service):
    from .helpers import model
    from .test_integration import setup

    one = await setup(hass)
    two = await setup(hass, model(id="two"))
    resources = hass.data[LOVELACE_DATA].resources
    before = resources.async_items().copy()
    assert len([r for r in before if r["url"].startswith(CARD_URL + "?")]) == 1
    assert await hass.config_entries.async_reload(one.entry_id)
    assert resources.async_items() == before
    assert await hass.config_entries.async_unload(one.entry_id)
    assert resources.async_items() == before and two.runtime_data.price_engine.records
    assert await hass.config_entries.async_unload(two.entry_id)


async def test_native_yaml_mode_keeps_resources_and_still_serves_card(
    hass, hass_storage, price_service, hass_client, caplog
):
    from homeassistant.setup import async_setup_component

    from .test_integration import setup

    items = [
        {"url": "/local/owner-card.js", "type": "module"},
        {"url": CARD_URL + "?v=1.0.0", "type": "module"},
    ]
    assert await async_setup_component(
        hass, "lovelace", {"lovelace": {"resource_mode": "yaml", "resources": items}}
    )
    resources = hass.data[LOVELACE_DATA].resources
    entry = await setup(hass)
    assert entry.runtime_data.price_engine.records
    assert resources.async_items() == items
    assert "lovelace_resources" not in hass_storage
    assert "YAML-managed" in caplog.text
    assert f"?v={entry.runtime_data.integration_version}" in caplog.text
    response = await (await hass_client()).get(CARD_URL)
    assert response.status == 200 and "energy-price-engine-card" in await response.text()
    assert await hass.config_entries.async_unload(entry.entry_id)
