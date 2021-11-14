""" Python script to generate and deploy Interface and BGP config for a link """

import yaml
import os
import time
import json
from jinja2 import Template
from nornir import InitNornir
from nornir_netmiko.tasks import netmiko_send_config
from nornir_napalm.plugins.tasks import napalm_get
from nornir_utils.plugins.functions import print_result

# Loading the input yaml file to a Dict
with open("bgp.yaml", 'r') as f:
    try:
        yml = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        print(exc)

# Loading the Jinja2 template file
with open("bgpconf.j2") as jin:
    jfile = jin.read()
conf = Template(jfile)

R1 = conf.render(int=yml['R1']['INT'], IP=yml['R1']['IP'], VLAN=yml['R1']['VLAN'], mask=yml['R1']['Mask'],
                 AS=yml['R1']['AS'], peer=yml['R2']['IP'], rmt_AS=yml['R2']['AS'])
R2 = conf.render(int=yml['R2']['INT'], IP=yml['R2']['IP'], VLAN=yml['R2']['VLAN'], mask=yml['R2']['Mask'],
                 AS=yml['R2']['AS'], peer=yml['R1']['IP'], rmt_AS=yml['R1']['AS'])

# Saving the rendered configs to a file which we will then load to netmiko_send_config
with open("R1_config", 'w') as cfg:
    cfg.write(R1)
with open("R2_config", 'w') as cfg:
    cfg.write(R2)

nr = InitNornir()

# yml.keys() will return the hosts from input yaml file, iterate through to run host specific tasks
for key in yml.keys():
    single_host = nr.inventory.hosts[key]
    rtr = nr.filter(hostname=single_host.dict()['hostname'])
    deploy = rtr.run(task=netmiko_send_config, config_file=f"{key}_config")
    print_result(deploy)
    os.remove(f"{key}_config")

# Wait for 15sec post deployment to capture the BGP stats from only the second router
time.sleep(15)
# Converting yml.keys() to list to retrieve the specific key using index
key1 = list(yml.keys())[0]
key2 = list(yml.keys())[1]
bgp_check = rtr.run(task=napalm_get, getters=['get_bgp_neighbors'])
bgp_result = bgp_check[key2][0].result

# Filtering the output to only extract peer relevant info to a Dict
bgp_output = bgp_result['get_bgp_neighbors']['global']['peers'][yml[key1]['IP']]

# Format the Dict to json to make it legible
json_output = json.dumps(bgp_output, indent=2)
print("=" * 50)
print(f"BGP Stats for the configured Peer {[yml[key1]['IP']][0]} (seen from {key2}) \n\n")
print(f"{json_output}")
print("=" * 50)
