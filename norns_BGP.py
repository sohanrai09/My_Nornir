from nornir import InitNornir
from nornir_napalm.plugins.tasks import napalm_get

nr = InitNornir()

output = nr.run(task=napalm_get, getters=['get_bgp_neighbors'])
# https://napalm.readthedocs.io/en/latest/base.html?highlight=bgp#napalm.base.base.NetworkDriver.get_bgp_neighbors

def BGP_peer_fn(BGP_x):
    for item,x in BGP_x.items():
        peers = BGP_x[item]['peers'] #_A dictionary with details of all available Peers_
        
        for peer,info in peers.items():  
            if BGP_x[item]['peers'][peer]['is_up'] == True:
                print(f"Peer_{BGP_x[item]['peers'][peer]['remote_as']} {peer} ({item}) is UP with an uptime of {int(BGP_x[item]['peers'][peer]['uptime']/60)} mins")
                
                try: #_Prefix counts for Peers in Global/Default routing table
                    print(f"\tAdvertised Prefixes : {BGP_x[item]['peers'][peer]['address_family']['ipv4 unicast']['sent_prefixes']}  ; Rcvd Prefixes : {BGP_x[item]['peers'][peer]['address_family']['ipv4 unicast']['accepted_prefixes']}\n")
                
                except: #_Prefix counts for Peers in VRF table
                    KeyError
                    print(f"\tAdvertised Prefixes : {BGP_x[item]['peers'][peer]['address_family']['vpnv4 unicast']['sent_prefixes']} ; Rcvd Prefixes : {BGP_x[item]['peers'][peer]['address_family']['vpnv4 unicast']['accepted_prefixes']}\n")

            else:
                print(f"Peer_{BGP_x[item]['peers'][peer]['remote_as']} {peer} ({item}) is DOWN!\n")

router_list = dict.keys(output)

for router in router_list:
    print(f"~~~~~~~ BGP Status on  {router} ~~~~~~~\n")
    R_result = output[router][0].result
    BGP = R_result['get_bgp_neighbors']
    BGP_peers = BGP_peer_fn(BGP)
