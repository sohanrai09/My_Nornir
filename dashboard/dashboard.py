from nornir import InitNornir
from nornir_pyez.plugins.tasks import pyez_rpc
from nornir_pyez.plugins.tasks import pyez_facts
from nornir_rich.progress_bar import RichProgressBar
from nornir.core.task import Task, Result
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.align import Align
import datetime
import re

now = datetime.datetime.now().strftime("%Y-%b-%d %H:%M:%S")

console = Console()

nr = InitNornir(config_file='config.yaml')
nr_with_processors = nr.with_processors([RichProgressBar()])


def validate_output(output_local, router_list_local):
    """
    Function to validate the output/result from the routers and determine the list of hosts
    on which the execution passed/failed.
    Returns list of hosts on which execution passed. If execution failed on any hosts, same will be displayed.
    """
    if output_local.failed:
        failed_hosts_local = [host for host in output_local.failed_hosts]
        passed_hosts_local = [rtr for rtr in router_list_local if rtr not in failed_hosts_local]
        console.print(f"\n[bold red]Task execution failed on :[/bold red] [bold blue] "
                      f"{failed_hosts_local}[/bold blue]\n")
    else:
        passed_hosts_local = router_list

    return passed_hosts_local


def main_task(task: Task) -> Result:
    """
    Nornir task which groups together all the individual tasks and
    returns Aggregated result
    """
    task.run(name='facts', task=pyez_facts)
    task.run(name='alarms', task=pyez_rpc, func='get-system-alarm-information')
    task.run(name='bgp', task=pyez_rpc, func='get-bgp-summary-information')
    task.run(name='isis', task=pyez_rpc, func='get-isis-adjacency-information')
    task.run(name='rib_fib', task=pyez_rpc, func='get-route-summary-information')
    task.run(name='memory', task=pyez_rpc, func='get-system-memory-information')
    task.run(name='cpu', task=pyez_rpc, func='get-route-engine-information')
    task.run(name='commit', task=pyez_rpc, func='get-commit-information')
    return Result(host=task.host)


main_result = nr_with_processors.run(task=main_task)
router_list = list(dict.keys(main_result))
passed_hosts = validate_output(main_result, router_list)
panel_list = []

# Iterating over list of passed hosts to extract the result for a particular host, which is a list of result for each
# individual task, ordered as per the tasks order in function 'main_task'
with console.status("Building dashboard...", spinner='point'):
    for router in passed_hosts:
        # Extracting system information
        facts_data = main_result[router][1].result
        version = facts_data.get('version')
        model = facts_data.get('model')
        serial_num = facts_data.get('serialnumber')
        re0 = facts_data.get('RE0')
        re1 = facts_data.get('RE1')  # Returns None if RE1 is not present
        if re0:
            re0_uptime = re0.get('up_time')
            re0_last_reboot_reason = re0.get('last_reboot_reason')
        else:
            re0_uptime = 'NA'
            re0_last_reboot_reason = 'NA'
        if re1:
            re1_uptime = re1.get('up_time')
            re1_last_reboot_reason = re1.get('last_reboot_reason')
        else:
            re1_uptime = 'NA'
            re1_last_reboot_reason = 'NA'

        # Extracting active alarms information
        alarms_data = main_result[router][2].result
        alarms_list_final = []
        try:
            alarms_var = alarms_data.get('alarm-information')['alarm-detail']
            if isinstance(alarms_var, list):
                for alarm in alarms_var:
                    alarms_list_final.append(alarm['alarm-description'])
            else:
                alarms_list_final.append(alarms_var['alarm-description'])
        except KeyError:
            alarms_list_final.append("None")

        sys_info_table = Table(show_lines=True, show_header=False, box=box.ASCII, title='System Information')
        sys_info_table.add_column("Field", justify="right", style="magenta", width=18)
        sys_info_table.add_column("Details", style="cyan", width=50)
        sys_info_table.add_row('SW version', version)
        sys_info_table.add_row('Model', model)
        sys_info_table.add_row('Serial Number', serial_num)
        sys_info_table.add_row('RE0 uptime', re0_uptime)
        sys_info_table.add_row('RE0 last reboot reason', re0_last_reboot_reason)
        sys_info_table.add_row('RE1 uptime', re1_uptime)
        sys_info_table.add_row('RE1 last reload reason', re1_last_reboot_reason)

        for alarm in alarms_list_final:
            sys_info_table.add_row('Active alarms', alarm)

        # Extracting routing Protocols Info
        bgp_data = main_result[router][3].result
        total_peers = bgp_data['bgp-information']['peer-count']
        down_peers = bgp_data['bgp-information']['down-peer-count']
        isis_data = main_result[router][4].result
        adj_up_count = 0
        adj_down_count = 0
        try:
            isis_list = isis_data['isis-adjacency-information']['isis-adjacency']
            for adj in isis_list:
                if adj.get('adjacency-state') == 'Up':
                    adj_up_count = adj_up_count + 1
                else:
                    adj_down_count = adj_down_count + 1
        except KeyError:  # This means ISIS is not configured
            adj_up_count = 'NA'
            adj_down_count = 'NA'

        # Extracting route information
        route_data = main_result[router][5].result
        rib_count = route_data['route-summary-information']['routing-highwatermark']['rt-all-highwatermark']
        fib_count = route_data['route-summary-information']['routing-highwatermark']['rt-fib-highwatermark']

        protocols_table = Table(show_lines=True, show_header=False, box=box.ASCII, width=47, title='Protocol Information')
        protocols_table.add_column("Field", justify="right", style="magenta")
        protocols_table.add_column("Details", style="cyan")
        protocols_table.add_row("BGP Peer UP count", str(int(total_peers) - int(down_peers)))
        protocols_table.add_row("BGP Peer DOWN count", down_peers)
        protocols_table.add_row("ISIS Adj UP count", str(adj_up_count))
        protocols_table.add_row("ISIS Adj DOWN count", str(adj_down_count))
        protocols_table.add_row("RIB routes", rib_count)
        protocols_table.add_row("FIB routes", fib_count)

        # Extracting CPU and memory info
        used_value, free_value, cpu_usage_list = [], [], [],
        memory_data = main_result[router][6].result
        free_mem = memory_data['system-memory-information']['system-memory-summary-information']['system-memory-free-percent']
        free_mem_int = int(re.sub('%', '', free_mem))
        used_mem = 100 - free_mem_int
        used_value.append(used_mem)
        free_value.append(free_mem_int)

        cpu_data = main_result[router][7].result
        cpu_check = cpu_data['route-engine-information']['route-engine']
        if isinstance(cpu_check, dict):  # This means device is having single RE
            cpu_usage = cpu_data['route-engine-information']['route-engine']['cpu-user']
            cpu_usage_list.append(int(cpu_usage))
        elif isinstance(cpu_check, list):  # This means device is having dual REs
            cpu_usage = cpu_data['route-engine-information']['route-engine'][0]['cpu-user']
            cpu_usage_list.append(int(cpu_usage))

        mem_cpu_table = Table(show_header=False, box=box.ASCII, width=50, title='Memory & CPU Information')
        mem_cpu_table.add_column("Field", justify="left", style="magenta")
        if used_mem > 20: # To reduce the number of emojis/diamonds displayed
            mem_cpu_table.add_row(":large_blue_diamond:" * (int(int(used_mem)/5)) + f" {used_mem}%" + "\n\n", style='cyan')
        else:
            mem_cpu_table.add_row(":large_blue_diamond:" * int(used_mem) + f" {used_mem}%" + "\n\n",
                                  style='cyan')
        if int(cpu_usage) > 20:
            mem_cpu_table.add_row(":large_orange_diamond:" * (int(int(cpu_usage)/2)) + f" {cpu_usage}%" + "\n\n\n",
                                  style='magenta')
        else:
            mem_cpu_table.add_row(":large_orange_diamond:" * int(int(cpu_usage)) + f" {cpu_usage}%" + "\n\n\n", style='magenta')
        mem_cpu_table.add_row(":large_blue_diamond:  memory in-use\t:large_orange_diamond:  cpu in-use")

        # Extracting commit info
        commit_data = main_result[router][8].result
        commit_user = commit_data['commit-information']['commit-history'][0]['user']
        commit_time = commit_data['commit-information']['commit-history'][0]['date-time']['#text']

        commit_table = Table(show_header=False, box=box.ASCII, width=50, title='Commit Information', style="blue")
        commit_table.add_column("Field", justify="left")
        commit_table.add_row("[cyan]Last commit by [/cyan]", f"[green]{commit_user}")
        commit_table.add_row("[cyan]\nLast commit at [/cyan]", f"\n[green]{commit_time}")

        mem_cpu_commit_table = Table(show_header=False, box=box.ASCII, width=53, show_edge=False)
        mem_cpu_commit_table.add_column("Field", justify="left", style="magenta")
        mem_cpu_commit_table.add_row(mem_cpu_table)
        mem_cpu_commit_table.add_row("\n")
        mem_cpu_commit_table.add_row(commit_table)

        # Everything comes together, all the tables are put into one main table, which is then rendered in a Panel
        main_table = Table(show_lines=True, show_header=False)
        main_table.add_column(justify="right", style="magenta")
        main_table.add_column(justify="right", style="green")
        main_table.add_column(justify="right", style="magenta")
        main_table.add_row(sys_info_table, protocols_table, mem_cpu_commit_table)

        panel = Panel(main_table, width=200,
                      title=router, box=box.DOUBLE)
        panel_list.append(panel)

# To display the date and time
console.print(Panel(Align.center(now), width=200, box=box.DOUBLE), style='red on white')

# Iterating over the list of panels i.e, panel per hosts and printing it to terminal
for pan in panel_list:
    console.print(pan)
