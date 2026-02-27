**CPU Scheduling Visualizer**

This project is an interactive CPU scheduling simulator built using Python. It demonstrates how different operating system scheduling algorithms manage processes and allocate CPU time.

The application includes a graphical user interface, real-time Gantt chart visualization, performance metrics, and algorithm comparison.

**Overview**

The simulator models how an operating system schedules processes using different CPU scheduling strategies.

Users can add processes, select an algorithm, and observe how execution unfolds. The system calculates important performance metrics and displays results in both tabular and graphical form.

The application uses threading to keep the interface responsive while simulations run.

**Implemented Algorithms**

The following scheduling algorithms are implemented:

**First Come First Serve (FCFS)**

**Shortest Job First (SJF) – Non-preemptive**

**Round Robin – Fixed quantum of 2**

For each process, the program calculates:

Start time

Completion time

Waiting time

Turnaround time

Performance Metrics

For every simulation run, the system calculates:

Average waiting time

Average turnaround time

CPU utilisation

Throughput

CPU idle time

There is also a comparison mode that runs all algorithms on the same dataset and displays their average waiting and turnaround times side by side.

**Features**

Real-time Gantt chart visualisation using Matplotlib

Multiple execution slices for Round Robin

Semaphore state display showing CPU lock and release

Live event log of scheduler actions

Results table displaying detailed timing metrics

Dark mode GUI built with Tkinter

Technologies Used

Python 3

Tkinter

Matplotlib

Threading

Dataclasses

**Project Structure**

CPU_Scheduler_All_Algorithms_GUI
│
├── main.py
├── requirements.txt
└── README.md

**How to Run**

Clone the repository
git clone https://github.com/your-username/CPU_Scheduler_All_Algorithms_GUI.git

Install dependencies
pip install -r requirements.txt

Run the application
python main.py

**Design Highlights**

Uses Python dataclasses to model processes

Thread-safe GUI updates through queued events

Efficient ready queue handling in Round Robin

Embedded Matplotlib charts inside Tkinter

Automatic calculation of scheduling metrics
