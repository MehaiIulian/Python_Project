import psutil
from datetime import datetime
import pandas as pd
import time
import os


def get_size(bytes):
    for unit in ['', 'K', 'M', 'G', 'T', 'P']:
        if bytes < 1024:
            return f"{bytes:.2f}{unit}B"
        bytes /= 1024


def get_processes_info():
    # the list the contain all process dictionaries
    processes = []
    for process in psutil.process_iter():
        # get all process info in one shot
        with process.oneshot():
            # get the process id
            pid = process.pid
            if pid == 0:
                # System Idle Process for Windows NT, useless to see anyways
                continue
            #print(pid)

            # get the name of the file executed
            name = process.name()
            #print(name)

            # get the time the process was spawned
            try:
                create_time = datetime.fromtimestamp(process.create_time())
            except OSError:
                # system processes, using boot time instead
                create_time = datetime.fromtimestamp(psutil.boot_time())
            #print(create_time)

            try:
                # get the number of CPU cores that can execute this process
                cores = len(process.cpu_affinity())
            except psutil.AccessDenied:
                cores = 0
            #print(cores)

            # get the CPU usage percentage
            cpu_usage = process.cpu_percent()
            #print(cpu_usage)

            # get the status of the process (running, idle, etc.)
            status = process.status()
            #print(status)

            try:
                # get the process priority (a lower value means a more prioritized process)
                nice = int(process.nice())
            except psutil.AccessDenied:
                nice = 0
            #print(nice)

            try:
                # get the memory usage in bytes
                memory_usage = process.memory_full_info().uss
            except psutil.AccessDenied:
                memory_usage = 0
            #print(memory_usage)

            # total process read and written bytes
            io_counters = process.io_counters()
            read_bytes = io_counters.read_bytes
            write_bytes = io_counters.write_bytes
            #print(f'Values:{io_counters},{read_bytes},{write_bytes}')

            # get the number of total threads spawned by this process
            n_threads = process.num_threads()
            #print(n_threads)

            # get the username of user spawned the process
            try:
                username = process.username()
            except psutil.AccessDenied:
                username = "N/A"
            #print(username)

            #get the path of the process executable
            path = process.exe()
            #print(path)

        processes.append({
            'pid': pid, 'name': name, 'create_time': create_time,
            'cores': cores, 'cpu_usage': cpu_usage, 'status': status, 'nice': nice,
            'memory_usage': memory_usage, 'read_bytes': read_bytes, 'write_bytes': write_bytes,
            'n_threads': n_threads,'path': path, 'username': username,
        })

    return processes


def construct_dataframe(processes):
    # convert to pandas dataframe
    df = pd.DataFrame(processes)
    # set the process id as index of a process
    df.set_index('pid', inplace=True)
    # sort rows by the column passed as argument
    df.sort_values(sort_by, inplace=True, ascending=not descending)
    # pretty printing bytes
    df['memory_usage'] = df['memory_usage'].apply(get_size)
    df['write_bytes'] = df['write_bytes'].apply(get_size)
    df['read_bytes'] = df['read_bytes'].apply(get_size)
    # convert to proper date format
    df['create_time'] = df['create_time'].apply(datetime.strftime, args=("%Y-%m-%d %H:%M:%S",))
    # reorder and define used columns
    return df


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Process Viewer & Monitor")
    parser.add_argument("-c", "--columns", help="""Columns to show,
                                                available are name,create_time,cores,cpu_usage,status,nice,memory_usage,read_bytes,write_bytes,n_threads,username.
                                                Default is name,cpu_usage,memory_usage,read_bytes,write_bytes,status,create_time,nice,n_threads,cores.""",
                        default="name,cpu_usage,memory_usage,read_bytes,write_bytes,status,create_time,nice,n_threads,cores,path,username")
    parser.add_argument("-s", "--sort-by", dest="sort_by", help="Column to sort by, default is memory_usage .",
                        default="memory_usage")
    parser.add_argument("--descending", action="store_true", help="Whether to sort in descending order.")
    parser.add_argument("-n", help="Number of processes to show, will show all if 0 is specified, default is 25 .",
                        default=sys.maxsize)
    parser.add_argument("-u", "--live-update", action="store_true",
                        help="Whether to keep the program on and updating process information each second.")
    parser.add_argument("--kill", action="store_true", help="Enter the process pid to kill.")
    parser.add_argument("--create", action="store_true", help="Enter the process pid to create.")
    parser.add_argument("--suspend", action="store_true", help="Enter the process pid to suspend.")
    parser.add_argument("--resume", action="store_true", help="Enter the process pid to resume.")

    # parse arguments
    args = parser.parse_args()
    print(args)
    columns = args.columns
    sort_by = args.sort_by
    descending = args.descending
    kill = args.kill
    create = args.create
    suspend = args.suspend
    resume = args.resume
    n = int(args.n)
    live_update = args.live_update
    # print the processes for the first time
    processes = get_processes_info()
    df = construct_dataframe(processes)

    if n == 0:
        print(df.to_string())
    elif n > 0:
        print(df.head(n).to_string())

    # print continuously
    while live_update:
        # get all process info
        processes = get_processes_info()
        df = construct_dataframe(processes)
        # clear the screen depending on your OS
        os.system("cls") if "nt" in os.name else os.system("clear")
        if n == 0:
            print(df.to_string())
        elif n > 0:
            print(df.head(n).to_string())
        time.sleep(0.7)
