import psutil
from datetime import datetime
import pandas as pd
import time
import os
import argparse


# return pids of a process
def get_pid(name):
    pids = []
    for proc in psutil.process_iter():
        if name in proc.name():
            pid = proc.pid
            pids.append(pid)
    return pids


# format for process size
def get_size(bytes):
    for unit in ['', 'K', 'M', 'G', 'T', 'P']:
        if bytes < 1024:
            return f"{bytes:.2f}{unit}B"
        bytes /= 1024


# current processes that run
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
            # print(pid)

            # get the name of the file executed
            name = process.name()
            # print(name)

            # get the time the process was spawned
            try:
                create_time = datetime.fromtimestamp(process.create_time())
            except OSError:
                # system processes, using boot time instead
                create_time = datetime.fromtimestamp(psutil.boot_time())
            # print(create_time)

            try:
                # get the number of CPU cores that can execute this process
                cores = len(process.cpu_affinity())
            except psutil.AccessDenied:
                cores = 0
            # print(cores)

            # get the CPU usage percentage
            cpu_usage = process.cpu_percent()
            # print(cpu_usage)

            # get the status of the process (running, idle, etc.)
            status = process.status()
            # print(status)

            try:
                # get the process priority (a lower value means a more prioritized process)
                nice = int(process.nice())
            except psutil.AccessDenied:
                nice = 0
            # print(nice)

            try:
                # get the memory usage in bytes
                memory_usage = process.memory_full_info().uss
            except psutil.AccessDenied:
                memory_usage = 0
            # print(memory_usage)

            # total process read and written bytes
            io_counters = process.io_counters()
            read_bytes = io_counters.read_bytes
            write_bytes = io_counters.write_bytes
            # print(f'Values:{io_counters},{read_bytes},{write_bytes}')

            # get the number of total threads spawned by this process
            n_threads = process.num_threads()
            # print(n_threads)

            # get the username of user spawned the process
            try:
                username = process.username()
            except psutil.AccessDenied:
                username = "N/A"
            # print(username)

            # get the path of the process executable
            path = process.exe()
            # print(path)

        processes.append({
            'pid': pid, 'name': name, 'path': path, 'create_time': create_time,
            'cores': cores, 'cpu_usage': cpu_usage, 'status': status, 'nice': nice,
            'memory_usage': memory_usage, 'read_bytes': read_bytes, 'write_bytes': write_bytes,
            'n_threads': n_threads, 'username': username,
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


def Convert(string):
    li = list(string.split(","))
    return li


def kill_process(name):
    for proc in psutil.process_iter():
        if name in proc.name():
            pid = proc.pid
            p = psutil.Process(pid)
            p.terminate()


def create_process(name):
    try:
        os.startfile(name)
    except FileNotFoundError:
        print("Please check the name or the path again")


def suspend_process(pid):
    try:
        psutil.Process(pid).suspend()
        print(f"Process with pid {pid} is {psutil.Process(pid).status()}")
    except psutil.NoSuchProcess():
        print("No process found with specified pid")
        pass


def resume_process(pid):
    try:
        psutil.Process(pid).resume()
        print(f"Process with pid {pid} is {psutil.Process(pid).status()}")
    except psutil.NoSuchProcess():
        print("No process found with specified pid")
        pass


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Process Viewer & Monitor & Operations")
    parser.add_argument("--columns", help="""Columns to display,pid is set as index and available columns are 
                                                name,create_time,cores,cpu_usage,status,nice,memory_usage,read_bytes,write_bytes,n_threads,username.
                                                Default is name,path.""",
                        default="name,path")
    parser.add_argument("--name", help="Name a process name to show details about it", default="")
    parser.add_argument("--sort-by", dest="sort_by", help="Column to sort by, default is memory_usage .",
                        default="memory_usage")
    parser.add_argument("--descending", action="store_true", help="Whether to sort in descending order.")
    parser.add_argument("--lines",
                        help="Number of processes to show, will show all if 0 is specified, default is -1 and shows nothing.Enter a value bigger than 0.",
                        default=-1)
    parser.add_argument("--live-update", action="store_true",
                        help="Whether to keep the program on and updating process information each second.Also please enter how many lines to show.")
    parser.add_argument("--kill", help="Enter the process name to kill.", default=0)
    parser.add_argument("--create", help="Enter the process name to create.", default=0)
    parser.add_argument("--suspend", help="Enter the process pid to suspend.", default=0)
    parser.add_argument("--resume", help="Enter the process pid to resume.", default=0)
    parser.add_argument("--pid", help="Get the pids of a process. Enter the process name", default="")

    # parse arguments
    args = parser.parse_args()
    columns = args.columns
    columns = Convert(columns)
    # print(columns)
    sort_by = args.sort_by
    descending = args.descending

    pid = args.pid
    pid = get_pid(pid)
    # print(pid)

    lines = int(args.lines)
    live_update = args.live_update

    # process operations
    kill = args.kill
    if kill != 0:
        kill_process(kill)

    create = args.create
    if create != 0:
        create_process(create)

    suspend = int(args.suspend)
    if suspend != 0:
        suspend_process(suspend)

    resume = int(args.resume)
    if resume != 0:
        resume_process(resume)

    # print the processes for the first time
    processes = get_processes_info()
    df = construct_dataframe(processes)

    # create a process list with specified name from command line
    name = args.name
    if name:
        print(name)

        if lines == 0:
            dfn = df.loc[df['name'] == name]
            print(dfn[columns].to_string())
        elif lines > 0:
            dfn = df.loc[df['name'] == name]
            df.loc[df['name'] == name]
            print(dfn[columns].head(lines).to_string())
        else:
            pass
    else:
        if lines == 0:
            print(df[columns].to_string())
        elif lines > 0:
            print(df[columns].head(lines).to_string())
        else:
            pass

    # print continuously
    while live_update:
        # get all process info
        processes = get_processes_info()
        df = construct_dataframe(processes)

        if name:
            print(name)

            if lines == 0:
                dfn = df.loc[df['name'] == name]
                print(dfn[columns].to_string())
            elif lines > 0:
                dfn = df.loc[df['name'] == name]
                df.loc[df['name'] == name]
                print(dfn[columns].head(lines).to_string())
        else:
            if lines == 0:
                print(df[columns].to_string())
            elif lines > 0:
                print(df[columns].head(lines).to_string())
        time.sleep(0.7)
