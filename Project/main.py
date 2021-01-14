import psutil
from datetime import datetime
import pandas as pd
import time
import os
import argparse


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
                continue

            # get the name of the file executed
            name = process.name()

            # get the time the process was spawned
            try:
                # spawned processes
                create_time = datetime.fromtimestamp(process.create_time())
            except OSError:
                # system processes
                create_time = datetime.fromtimestamp(psutil.boot_time())

            try:
                # get the number of CPU cores that can execute this process
                cores = len(process.cpu_affinity())
            except psutil.AccessDenied:
                cores = 0

            cpu_usage = process.cpu_percent()

            # get the status of the process
            status = process.status()

            try:
                # get the process priority (a lower value means a more prioritized process)
                nice = int(process.nice())
            except psutil.AccessDenied:
                nice = 0

            try:
                # get the memory usage in bytes
                memory_usage = process.memory_full_info().uss
            except psutil.AccessDenied:
                memory_usage = 0

            # total process read and written bytes
            io_counters = process.io_counters()
            read_bytes = io_counters.read_bytes
            write_bytes = io_counters.write_bytes

            # get the number of total threads spawned by this process
            n_threads = process.num_threads()

            # get the username of user spawned the process
            try:
                username = process.username()
            except psutil.AccessDenied:
                username = "N/A"

            # get the path of the process executable
            path = process.exe()

        processes.append({
            'pid': pid, 'name': name, 'path': path, 'create_time': create_time,
            'cores': cores, 'cpu_usage': cpu_usage, 'status': status, 'nice': nice,
            'memory_usage': memory_usage, 'read_bytes': read_bytes, 'write_bytes': write_bytes,
            'n_threads': n_threads, 'username': username,
        })

    return processes


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


# convert columns string to a list
def Convert(string):
    li = list(string.split(","))
    return li


# process killer
def kill_process(name):
    for proc in psutil.process_iter():
        if name in proc.name():
            pid = proc.pid
            p = psutil.Process(pid)
            p.terminate()


# process creator
def create_process(name):
    try:
        os.startfile(name)
    except FileNotFoundError:
        print("Please check the name or the path again")


# process "suspender"
def suspend_process(pid):
    try:
        psutil.Process(pid).suspend()
        print(f"Process with pid {pid} is {psutil.Process(pid).status()}")
    except psutil.NoSuchProcess(pid):
        print("No process found with specified pid")
        pass


# process "resumer"
def resume_process(pid):
    try:
        psutil.Process(pid).resume()
        print(f"Process with pid {pid} is {psutil.Process(pid).status()}")
    except psutil.NoSuchProcess(pid):
        print("No process found with specified pid")
        pass


def construct_dataframe(processes):
    df = pd.DataFrame(processes)

    # set pid as index
    df.set_index('pid', inplace=True)

    # sort rows by the column passed as argument
    df.sort_values(sort_by, inplace=True, ascending=not descending)

    # converting bytes in a nice format
    df['memory_usage'] = df['memory_usage'].apply(get_size)
    df['write_bytes'] = df['write_bytes'].apply(get_size)
    df['read_bytes'] = df['read_bytes'].apply(get_size)

    # convert to proper date format
    df['create_time'] = df['create_time'].apply(datetime.strftime, args=("%Y-%m-%d %H:%M:%S",))

    return df


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Process Viewer & Monitor & Operations")
    parser.add_argument("--kill", help="Enter the process name to kill.", default=0)
    parser.add_argument("--create", help="Enter the process name to create.", default=0)
    parser.add_argument("--suspend", help="Enter the process pid to suspend.", default=0)
    parser.add_argument("--resume", help="Enter the process pid to resume.", default=0)
    parser.add_argument("--pid", help="Get the pids of a process. Enter the process name.", default="")
    parser.add_argument("--columns", help="""Columns to display,pid is set as index and available columns are 
                                                name,path,create_time,cores,cpu_usage,status,nice,memory_usage,read_bytes,write_bytes,n_threads,username.
                                                Default is name,path.""",
                        default="name,path")
    parser.add_argument("--name", help="Write the name of a process to display details about it.", default="")
    parser.add_argument("--sort-by", dest="sort_by", help="Column to sort by, default is memory_usage.",
                        default="memory_usage")
    parser.add_argument("--descending", action="store_true", help="Whether to sort in descending order.")
    parser.add_argument("--lines",
                        help="***IMPORTANT*** Write the number of processes to display, "
                             "will show all if 0 is specified, default is -1. If "" --lines "" "
                             "is not used, then the program will not display anything"
                             "(PROCESSES CAN BE DISPLAYED WITH -1 ONLY WHEN LIVE_UPDATING).",
                        default=-1)
    parser.add_argument("--live-update", action="store_true",
                        help="Whether to keep the program on and updating process information each second.")

    # parse arguments
    args = parser.parse_args()
    columns = args.columns
    columns = Convert(columns)

    sort_by = args.sort_by
    descending = args.descending

    pid = args.pid
    if pid:
        print(get_pid(pid))

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
        if lines == 0:
            dfn = df.loc[df['name'] == name]
            print(dfn[columns].to_string())
        elif lines > 0:
            dfn = df.loc[df['name'] == name]
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

        message = "  *_*_* updating.. *_*_*  "
        print(message)
        rows = len(message)
        print("*" * rows, end="\n")
        i = (rows // 2) - 1
        j = 2
        while i != 0:
            while j <= (rows - 2):
                print("*" * i, end="")
                print("_" * j, end="")
                print("*" * i, end="\n")
                i = i - 1
                j = j + 2

        if name:
            if lines == 0 or lines == -1:
                dfn = df.loc[df['name'] == name]
                print(dfn[columns].to_string())
            elif lines > 0:
                dfn = df.loc[df['name'] == name]
                print(dfn[columns].head(lines).to_string())
        else:
            if lines == 0 or lines == -1:
                print(df[columns].to_string())
            elif lines > 0:
                print(df[columns].head(lines).to_string())
        time.sleep(0.7)
