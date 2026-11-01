"""Use HA's supported authenticated local brand route; no HACS/CDN substitution."""

from pathlib import Path

from homeassistant.setup import async_setup_component

from .test_integration import setup


async def test_native_local_brand_assets(hass, price_service, hass_client, hass_access_token):
    entry = await setup(hass)
    assert await async_setup_component(hass, "brands", {})
    client = await hass_client()
    for name in ("icon.png", "logo.png", "dark_icon.png", "dark_logo@2x.png"):
        response = await client.get(
            f"/api/brands/integration/ha_energy_price_engine/{name}",
            headers={"Authorization": f"Bearer {hass_access_token}"},
        )
        assert response.status == 200
        assert (
            await response.read()
            == (Path("custom_components/ha_energy_price_engine/brand") / "icon.png").read_bytes()
        )
    assert await hass.config_entries.async_unload(entry.entry_id)
