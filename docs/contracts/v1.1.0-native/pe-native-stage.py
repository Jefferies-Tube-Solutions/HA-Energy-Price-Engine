import asyncio, json, sys, hashlib, logging
from pathlib import Path
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import patch

logging.basicConfig(level=logging.WARNING)
root=Path(sys.argv[1]); stage=sys.argv[2]
sys.path.insert(0,str(root))
async def main():
    from homeassistant.core import HomeAssistant
    from homeassistant import bootstrap, loader
    from homeassistant.helpers import frame
    from homeassistant.util import dt
    now=datetime(2026,11,1,10,15,tzinfo=UTC)
    # Change only PE's local clock references; HA auth/wall clock is untouched.
    clock=SimpleNamespace(**{n:getattr(dt,n) for n in dir(dt) if not n.startswith('__')})
    clock.utcnow=lambda: now
    clock.now=lambda: now
    import importlib
    for name in ('api','coordinator','dashboard','price_schedule','status','sensor','config_flow'):
        module=importlib.import_module('custom_components.ha_energy_price_engine.'+name)
        module.dt_util=clock
    schedule_module=importlib.import_module('custom_components.ha_energy_price_engine.price_schedule')
    from homeassistant.helpers.event import async_track_point_in_utc_time
    from datetime import timedelta
    def relative_timer(hass, action, point):
        return async_track_point_in_utc_time(hass, action, dt.utcnow()+max(point-now,timedelta(seconds=1)))
    schedule_module.async_track_point_in_utc_time=relative_timer
    async def synthetic_provider_only(hass):
        assert str(hass.config.config_dir)==str(root)
    importlib.import_module('custom_components.ha_energy_price_engine.prices').ensure_official_nordpool=synthetic_provider_only
    hass=HomeAssistant(str(root))
    loader.async_setup(hass); frame.async_setup(hass)
    config={'homeassistant':{'name':'PE Disposable QA','latitude':55.7,'longitude':12.6,'elevation':0,'unit_system':'metric','time_zone':'Europe/Copenhagen','country':'DK'},'http':{'server_host':'127.0.0.1','server_port':8134},'api':{},'lovelace':{},'frontend':{}}
    assert await bootstrap.async_from_config_dict(config,hass)
    await hass.async_start()
    await hass.async_block_till_done()
    entries=hass.config_entries.async_entries('ha_energy_price_engine')
    assert len(entries)==3
    from homeassistant.config_entries import ConfigEntryState
    from homeassistant.helpers import entity_registry as er
    from homeassistant.components.lovelace.const import LOVELACE_DATA
    from custom_components.ha_energy_price_engine.dashboard import price_schedule
    assert all(e.state==ConfigEntryState.LOADED for e in entries), [(e.entry_id,e.state) for e in entries]
    resources=hass.data[LOVELACE_DATA].resources
    await resources.async_load()
    snapshots=[]
    for entry in entries:
        c=entry.runtime_data
        ids=sorted((e.entity_id,e.unique_id) for e in er.async_entries_for_config_entry(er.async_get(hass),entry.entry_id))
        assert len(ids)==23
        schedule=price_schedule(c,now)
        assert schedule['days'][0]['slots']
        assert c.price_engine.records[c.site['id']], schedule['days'][0]
        snapshots.append({'entry_id':entry.entry_id,'settings':dict(entry.data),'options':dict(entry.options),'entities':ids,'schedule':schedule,'ledger':str(c.price_engine.database.path),'sha256':hashlib.sha256(c.price_engine.database.path.read_bytes()).hexdigest()})
    before=resources.async_items().copy()
    for entry in entries: assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert resources.async_items()==before
    for entry,snap in zip(entries,snapshots):
        assert hashlib.sha256(entry.runtime_data.price_engine.database.path.read_bytes()).hexdigest()==snap['sha256']
    result={'stage':stage,'version':json.loads((root/'custom_components/ha_energy_price_engine/manifest.json').read_text())['version'],'resources':before,'sites':snapshots,'reload_preserved':True}
    (root/(stage+'.json')).write_text(json.dumps(result,indent=2))
    import os
    if os.environ.get('PE_NATIVE_HOLD'):
        source_calls=[]
        original_call=hass.services.async_call
        async def monitor(registry,domain,service,*args,**kwargs):
            if domain=='nordpool': source_calls.append(service)
            return await original_call(domain,service,*args,**kwargs)
        service_patch=patch.object(type(hass.services),'async_call',monitor)
        service_patch.start()
        user=await hass.auth.async_create_user('Disposable QA', group_ids=['system-admin'])
        refresh=await hass.auth.async_create_refresh_token(user, client_id='http://127.0.0.1:8134/')
        token=hass.auth.async_create_access_token(refresh)
        token_file=root/'qa-access-token'
        token_file.write_text(token); token_file.chmod(0o600)
        (root/'ready').write_text(stage)
        while not (root/'stop').exists(): await asyncio.sleep(0.2)
        token_file.unlink()
        service_patch.stop()
        assert source_calls==[], source_calls
        (root/'browser-no-source-reads.json').write_text(json.dumps({'provider_reads':len(source_calls)}))
    # Native stores persist on real shutdown, unlike pytest's mocked storage.
    await hass.async_stop()
    print('Native stage passed:',stage,flush=True)
asyncio.run(main())
