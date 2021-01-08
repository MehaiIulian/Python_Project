import wmi
import psutil

def A():
    # Initializing the wmi constructor
    f = wmi.WMI()

    # Printing the header for the later columns
    print("PID PROCESS_NAME PATH")

    # Iterating through all the running processes
    for process in f.Win32_Process():
        p = psutil.Process(int(process.ProcessId))
        try:
            path = p.exe()
        except:
            path = "-"

        print(f"{process.ProcessId} {process.Name} {path}")

if __name__ == "__main__":
    A()
