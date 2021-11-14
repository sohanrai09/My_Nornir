''' This script fetches BGP neighbour details such as Peer Status, Uptime, Peer AS, VRF/Global, Prefix counters.
References:
Working with NORNIR objects,results etc. https://gist.github.com/danielmacuare/c647880cfc99a605d25c3b669ab63fc7
NORNIR Plugins https://nornir.tech/nornir/plugins/ '''


from nornir import InitNornir
from nornir_napalm.plugins.tasks import napalm_get
import time
import pandas as pd
from tabulate import tabulate

Start = time.time()

nr = InitNornir()
# https://nornir.readthedocs.io/en/3.0.0/index.html#

output = nr.run(task=napalm_get, getters=['get_bgp_neighbors'])
# https://napalm.readthedocs.io/en/latest/base.html?highlight=bgp#napalm.base.base.NetworkDriver.get_bgp_neighbors

mydict = {'Router':[],'Neighour':[],'Remote_AS':[],'VRF':[],'Status':[],'Uptime(mins)':[],'Advertised Prefixes':[],'Rcvd Prefixes':[]}
# Creating a Dict to capture the output and then feed it to Pandas to create a dataframe.


def BGP_peer_fn(BGP_x):
    
    for item,x in BGP_x.items():
        #This dict has 'global' and 'VRF' as keys, iterating thorugh them
        
        peers = BGP_x[item]['peers']
        
        for peer,info in peers.items():
            # Iterating through each peer/neighbour
            
            rm_as = BGP_x[item]['peers'][peer]['remote_as']
            mydict['Router'].append(router)
            mydict['Neighour'].append(peer)
            mydict['Remote_AS'].append(rm_as)
            mydict['VRF'].append(item)
            
            if BGP_x[item]['peers'][peer]['is_up'] == True:
                # If Peer is UP, proceeding to collect Prefix counters and uptime
                
                upt = int(BGP_x[item]['peers'][peer]['uptime']/60)
                mydict['Status'].append('UP')
                mydict['Uptime(mins)'].append(upt)
                
                try:
                    # Prefix counters for 'Global' Peers
                    
                    adv= BGP_x[item]['peers'][peer]['address_family']['ipv4 unicast']['sent_prefixes']
                    Rcvd = BGP_x[item]['peers'][peer]['address_family']['ipv4 unicast']['accepted_prefixes']
                    mydict['Advertised Prefixes'].append(adv)
                    mydict['Rcvd Prefixes'].append(Rcvd)
                    
                except:
                    KeyError
                    # Prefix counters for 'VRF' Peers
                    
                    adv = BGP_x[item]['peers'][peer]['address_family']['vpnv4 unicast']['sent_prefixes']
                    Rcvd = BGP_x[item]['peers'][peer]['address_family']['vpnv4 unicast']['accepted_prefixes']
                    mydict['Advertised Prefixes'].append(adv)
                    mydict['Rcvd Prefixes'].append(Rcvd)
                    
            else:
                # If Peer is DOWN, other values will not be available
                
                mydict['Status'].append('DOWN')
                mydict['Uptime(mins)'].append('NA')
                mydict['Advertised Prefixes'].append('NA')
                mydict['Rcvd Prefixes'].append('NA')
                
router_list = dict.keys(output)
# NORNIR output is a Dict with keys as per 'hosts.yaml' file, check the reference link at the top to know more.

for router in router_list:
    R_result = output[router][0].result
    BGP = R_result['get_bgp_neighbors']
    BGP_peers = BGP_peer_fn(BGP)

df = pd.DataFrame(mydict)
# Creating Pandas Dataframe from the Output dict collected

End = time.time()

print("\n")

print(tabulate(df,headers='keys',tablefmt='psql'))
# Formating Dataframe using Tabulate https://pypi.org/project/tabulate/

print(f"\nScript exec time : {End-Start}\n")
