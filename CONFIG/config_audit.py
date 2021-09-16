from nornir import InitNornir
from nornir_napalm.plugins.tasks import napalm_get,napalm_cli
import time,re
Start = time.time()
nr = InitNornir()
output = nr.run(task=napalm_get, getters=['get_config'])
def save_fn(Conf):
    Runn_reg = re.search(r'version 15.6.*end',Conf['running'],re.DOTALL)
    Start_reg = re.search(r'version 15.6.*end',Conf['startup'],re.DOTALL)
    Startup = Start_reg.group(0)
    Runn = Runn_reg.group(0)
    if Runn == Startup:
        print(f"\n~~~~~~~ Config up-to-date on {router} ~~~~~~~\n")
    else:
        wr = ['wr mem']
        nr.run(task=napalm_cli, commands=[wr])
        print(f"\n~~~~~~~ Config saved on {router} ~~~~~~~\n")
router_list = dict.keys(output)
for router in router_list:
    Conf_result = output[router][0].result
    Final_Conf = Conf_result['get_config']
    save_fn(Final_Conf)
End = time.time()
print(f"Script exec time : {End-Start}")