"""Maintain the bundled card's one storage resource through native Lovelace APIs."""

import asyncio
import logging
from urllib.parse import urlencode, urlsplit

from homeassistant.components.lovelace.const import LOVELACE_DATA, MODE_STORAGE
from homeassistant.loader import async_get_integration

from .const import DOMAIN

CARD_URL = "/ha_energy_price_engine/energy-price-engine-card.js"
LOGGER = logging.getLogger(__name__)


def _owned(url):
    parsed = urlsplit(url)
    return not parsed.scheme and not parsed.netloc and parsed.path == CARD_URL


async def async_register_card(hass):
    """Load before inspecting; adopt only our exact local path, never delete resources.

    This optional UI feature must not stop price production. Cancellation still
    propagates, and every failed registration reports the corrective action.
    """
    url = CARD_URL
    try:
        version = (await async_get_integration(hass, DOMAIN)).version
        if not version:
            raise ValueError("Installed integration manifest has no version")
        url += "?" + urlencode({"v": str(version)})
        async with hass.data.setdefault(DOMAIN + "_resource_lock", asyncio.Lock()):
            lovelace = hass.data[LOVELACE_DATA]
            if lovelace.resource_mode != MODE_STORAGE:
                LOGGER.info(
                    "Lovelace resources are YAML-managed. Add url: %s with type: module "
                    "under lovelace.resources, then reload resources. PE does not edit YAML.",
                    url,
                )
                return
            collection = lovelace.resources
            await collection.async_get_info()  # Explicit public lazy-load barrier.
            matches = [item for item in collection.async_items() if _owned(item["url"])]
            if len(matches) > 1:
                LOGGER.warning(
                    "Found %s bundled PE resources (%s). Keep one resource for %s in "
                    "Settings > Dashboards > Resources, then restart HA. No resources "
                    "were changed; pricing continues.",
                    len(matches),
                    ", ".join(item["id"] for item in matches),
                    url,
                )
                return
            if matches:
                item = matches[0]
                if item["url"] != url or item["type"] != "module":
                    await collection.async_update_item(
                        item["id"], {"url": url, "res_type": "module"}
                    )
            else:
                await collection.async_create_item({"url": url, "res_type": "module"})
    except Exception as err:
        LOGGER.warning(
            "Could not register the optional PE Lovelace module %s: %s: %s. "
            "Pricing continues. Add this URL as a JavaScript module in Settings > "
            "Dashboards > Resources (or lovelace.resources for YAML), and check HA "
            "storage permissions/logs before restarting HA to retry.",
            url,
            type(err).__name__,
            err,
            exc_info=True,
        )
