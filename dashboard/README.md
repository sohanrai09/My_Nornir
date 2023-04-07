## Network Dashboard


This script was developed as a fun little exercise to explore the network automation possibilities with [Nornir](https://nornir.readthedocs.io/) and [Rich](https://rich.readthedocs.io/en/stable/index.html). 

There are two main sections to this, one, fetching the network information for which I'll be using Juniper [PyEZ](https://www.juniper.net/documentation/product/us/en/junos-pyez/). Two, building the dashboard itself using Rich. Although in this script I'm using Juniper devices, with few changes this can be repurposed for other vendor devices as well.

As of now, Dashboard covers the following sections.

- General System Information
- Routing Protocol Information (BGP, ISIS, Global RIB/FIB)
- Memory & CPU Utilization
- Configuration commit information (Last Change)

I have covered the details of the script in my [blog post](https://sohanrai09.github.io/new-blog/2023/04/network-dashboard/).

### Final Output

![dashboard_1](https://github.com/sohanrai09/My_Nornir/blob/main/dashboard/dashboard_1.png)
![dashboard_2](https://github.com/sohanrai09/My_Nornir/blob/main/dashboard/dashboard_2.png)

### Dashboard in action


https://user-images.githubusercontent.com/89385413/230535408-f8bcdbdd-a425-41cd-a42b-f8b38acb2a1a.mov


