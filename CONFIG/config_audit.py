''' This script checks if the running config on the device is saved, if it's not, config is saved.'''

from nornir import InitNornir
from nornir_napalm.plugins.tasks import napalm_get,napalm_cli
import time,re

Start = time.time()

nr = InitNornir()

# https://napalm.readthedocs.io/en/latest/base.html?highlight=config#napalm.base.base.NetworkDriver.get_config
output = nr.run(task=napalm_get, getters=['get_config'])


def save_fn(Conf):
    
    # Regex to find just the configuration and not the timestamps usually present at the top
    Runn_reg = re.search(r'version 15.*end',Conf['running'],re.DOTALL)
    Start_reg = re.search(r'version 15.*end',Conf['startup'],re.DOTALL)
    Startup = Start_reg.group(0)
    Runn = Runn_reg.group(0)
    
    if Runn == Startup:
        print(f"\n~~~~~~~ Config up-to-date on {router} ~~~~~~~\n")
        
    else:
        
        # https://napalm.readthedocs.io/en/latest/base.html?highlight=config#napalm.base.base.NetworkDriver.cli
        wr = ['wr mem']
        nr.run(task=napalm_cli, commands=[wr])
        # Using NAPALM CLI option, sending "wr mem" to save the running configuration
        
        print(f"\n~~~~~~~ Config saved on {router} ~~~~~~~\n")
        
        
router_list = dict.keys(output) # Nornir output is a Dict with keys from hosts.yaml as keys.

for router in router_list:
    Conf_result = output[router][0].result
    Final_Conf = Conf_result['get_config']
    save_fn(Final_Conf)
    
End = time.time()
print(f"Script exec time : {End-Start}")
