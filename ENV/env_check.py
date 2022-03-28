''' This script fetches device/router details such as CPU, RAM, Last reload time, Last reload reason and finally performs
a configuration backup to text file.
References:
Working with NORNIR Objects,results etc. https://gist.github.com/danielmacuare/c647880cfc99a605d25c3b669ab63fc7
NORNIR Plugins https://nornir.tech/nornir/plugins/ '''


from nornir import InitNornir
from nornir_napalm.plugins.tasks import napalm_get
from nornir_netmiko.tasks import netmiko_send_command
from tabulate import tabulate
import pandas as pd
import re,datetime


Start = datetime.datetime.now()

mydict = {'Router':[],'CPU':[],'RAM':[],'Uptime':[],'Last_Reload':[],'Last_Change':[],'Conf_backup':[]}
# Creating a Dict to capture the output and then feed it to Pandas to create a dataframe.

nr = InitNornir()
# https://nornir.readthedocs.io/en/3.0.0/index.html#

output = nr.run(task=napalm_get, getters=['get_environment','get_facts','get_config'])
# https://napalm.readthedocs.io/en/latest/base.html#

reason = nr.run(task=netmiko_send_command,command_string='sh version | i reload.reason')
Last_change = nr.run(task=netmiko_send_command,command_string='sh startup-config | i Last.*change')
# https://pynet.twb-tech.com/blog/automation/netmiko.html


def Env_fn(Env,Rns,Last_Ch):
    # Function to gather Environment details such as RAM,CPU and reason for last reload along with Last change occurance.

    CPU = Env['get_environment']['cpu'][0][f'%usage']
    RAM = (Env['get_environment']['memory']['used_ram']/Env['get_environment']['memory']['available_ram'])*100
    Uptime = Env['get_facts']['uptime']
    reload = re.search(":\s(.*)",Rns).group(1)
    Last_CHG = re.search("at\s(.*)",Last_Ch).group(1)

    
    if Uptime in range(60,3600):
        Uptime = str(Uptime/60)+' Min'
        
    else:
        Uptime = str(round(Uptime/3600,2))+' Hr'

        
    mydict['Router'].append(router)
    mydict['CPU'].append(CPU)
    mydict['RAM'].append(int(RAM))
    mydict['Uptime'].append(Uptime)
    mydict['Last_Reload'].append(reload)
    mydict['Last_Change'].append(Last_CHG)
    # appending values to Dict


router_list = dict.keys(output)


for router in router_list:
    Env = output[router][0].result
    Rns = reason[router][0].result
    Last_Ch = Last_change[router][0].result
    Env_fn(Env,Rns,Last_Ch)

    Runn_config = Env['get_config']['running']
    backup = open(f"Conf_backup/{router}_{Start}.txt",'w')
    backup.write(Runn_config)
    backup.close()
    mydict['Conf_backup'].append(f"{router}_{Start}.txt")
    # Fetching running config and storing it locally


df = pd.DataFrame(mydict)
# Creating Pandas Dataframe from the Output dict collected

End = datetime.datetime.now()

print("\n")
print(tabulate(df,headers='keys',tablefmt='psql'))
print(f"\nScript exec time : {End-Start}\n")
