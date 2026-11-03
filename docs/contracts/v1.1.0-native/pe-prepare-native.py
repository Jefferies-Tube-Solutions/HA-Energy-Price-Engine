from pathlib import Path
import json,zipfile,sys
from pytest_homeassistant_custom_component.common import MockConfigEntry
r=Path('/tmp/pe-v11-native');r.mkdir(exist_ok=True)
with zipfile.ZipFile('/tmp/pe-public-beta/ha_energy_price_engine.zip') as z:z.extractall(r/'custom_components/ha_energy_price_engine')
np=r/'custom_components/nordpool';np.mkdir(parents=True,exist_ok=True)
(np/'manifest.json').write_text(json.dumps({'domain':'nordpool','name':'Synthetic QA only','version':'1.0.0','codeowners':[],'dependencies':[],'requirements':[]}))
(np/'__init__.py').write_text('''from homeassistant.core import SupportsResponse
from datetime import datetime,timedelta
async def async_setup_entry(hass,entry):
    async def prices(call):
        from custom_components.ha_energy_price_engine.price_engine import day_bounds
        start,end=day_bounds(datetime.fromisoformat(call.data['date']).date())
        rows=[]
        while start<end:
            rows.append({'start':start.isoformat(),'end':(start+timedelta(minutes=15)).isoformat(),'price':-100})
            start+=timedelta(minutes=15)
        return {'DK2':rows}
    hass.services.async_register('nordpool','get_prices_for_date',prices,supports_response=SupportsResponse.ONLY)
    return True
async def async_unload_entry(hass,entry):return True
''')
# Export the existing repository's fictional test model, never user/site data.
sys.path.insert(0,'/workspace/HA-Energy-Price-Engine')
from tests.helpers import model
entries=[MockConfigEntry(domain='nordpool',entry_id='np',data={'areas':['DK2'],'currency':'DKK'}).as_dict()]
for i in range(3): entries.append(MockConfigEntry(domain='ha_energy_price_engine',entry_id=f'qa-pe-site-{i}',unique_id=f'qa_{i}',version=4,data=model(id=f'qa_{i}',name=f'Fictional QA {i}',display_including_vat=i!=1)).as_dict())
s=r/'.storage';s.mkdir(exist_ok=True)
(s/'core.config_entries').write_text(json.dumps({'version':1,'minor_version':5,'key':'core.config_entries','data':{'entries':entries}}))
(s/'lovelace_resources').write_text(json.dumps({'version':1,'minor_version':1,'key':'lovelace_resources','data':{'items':[{'id':'before','url':'/local/qa-before.js','type':'module'},{'id':'adopted','url':'/ha_energy_price_engine/energy-price-engine-card.js?v=1.1.0-beta.1','type':'module'},{'id':'after','url':'/local/qa-after.js','type':'module'}]}}))
(r/'configuration.yaml').write_text('')
