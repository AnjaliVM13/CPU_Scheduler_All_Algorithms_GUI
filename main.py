"""
CPU Scheduling Simulator with Semaphore Control and Gantt Charts
-------------------------------------------------------------------

Description:
    A CPU scheduling simulator built with Tkinter and Matplotlib.
    Supports three scheduling algorithms (FCFS, SJF, Round Robin) with real-time
    visualization, Gantt charts, semaphore state display, and CPU performance metrics.

Key Features:
    • Three scheduling algorithms: FCFS, SJF, Round Robin
    • Real-time Gantt chart timeline visualization
    • Automatic calculation of waiting, turnaround, and completion time
    • CPU metrics: utilization, throughput, and idle time tracking
    • Semaphore panel showing CPU state and current running process
    • Live event log showing scheduler actions
    • Threaded simulation engine for smooth and responsive UI

-------------------------------------------------------------------
"""

# -------------------- Standard Library --------------------
import threading  # Threading for concurrent execution
from dataclasses import dataclass  # Dataclass decorator for simple data structures
from typing import List  # Type hinting

import tkinter as tk  # GUI components
from tkinter import ttk  # Themed widgets

# -------------------- Third-Party Libraries --------------------
import matplotlib.pyplot as plt  # Plotting charts
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
)  # Embed matplotlib in Tkinter


# -------------------- Process Data Structure --------------------
@dataclass
class Process:
    pid: int  # Process ID
    arrival: int  # Arrival time of process
    burst: int  # Burst (execution) time of process
    start: int = None  # Start time (initialized later)
    completion: int = None  # Completion time (initialized later)
    waiting: int = None  # Waiting time (initialized later)
    turnaround: int = None  # Turnaround time (initialized later)
    slices: list = None  # For RR, stores multiple time slices

    # Ensure slices is always initialized
    def __post_init__(self):
        if self.slices is None:
            self.slices = []


# -------------------- Main Scheduler Application --------------------
class SchedulerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CPU Scheduler with Semaphore (Dark Mode)")
        self.root.configure(bg="#1e1e1e")
        self.root.geometry("1300x750")

        # -------------------- App State --------------------
        self.processes: List[Process] = []  # List of all processes
        self.pid_counter = 1  # Auto-increment PID
        self.threaded_events = []  # Thread-safe GUI update queue

        # ---------- Top Input Section ----------
        top = tk.Frame(root, bg="#1e1e1e")
        top.pack(pady=10)

        # ---------- Arrival + Burst inputs ----------
        tk.Label(top, text="Arrival Time:", fg="white", bg="#1e1e1e").grid(
            row=0, column=0
        )
        self.arrival_entry = tk.Entry(top, width=5)
        self.arrival_entry.grid(row=0, column=1, padx=5)
        self.arrival_entry.insert(0, "0")
        self.arrival_entry.config(state="disabled")  # Always 0, uneditable

        tk.Label(top, text="Burst Time:", fg="white", bg="#1e1e1e").grid(
            row=0, column=2
        )
        self.burst_entry = tk.Entry(top, width=5)
        self.burst_entry.grid(row=0, column=3, padx=5)

        # ---------- Algorithm dropdown ----------
        tk.Label(top, text="Algorithm:", fg="white", bg="#1e1e1e").grid(row=0, column=4)
        self.alg_option = ttk.Combobox(
            top, values=["FCFS", "SJF", "Round Robin"], width=12
        )
        self.alg_option.grid(row=0, column=5, padx=5)
        self.alg_option.current(0)
        self.alg_option.bind(
            "<<ComboboxSelected>>", self._toggle_quantum
        )  # Enable/disable quantum

        # ---------- Quantum input (for Round Robin Only) ----------
        tk.Label(top, text="Quantum:", fg="white", bg="#1e1e1e").grid(row=0, column=6)
        self.quantum_entry = tk.Entry(top, width=5)
        self.quantum_entry.grid(row=0, column=7, padx=5)
        self.quantum_entry.insert(0, "2")
        self.quantum_entry.config(state="disabled")  # Fixed value

        # ---------- Action Buttons ----------
        tk.Button(
            top, text="Add Process", command=self.add_process, bg="#3a3a3a", fg="white"
        ).grid(row=0, column=8, padx=5)
        tk.Button(
            top,
            text="Run Scheduler",
            command=self.run_algorithm,
            bg="#007acc",
            fg="white",
        ).grid(row=0, column=9, padx=5)
        tk.Button(
            top, text="Clear All", command=self.clear_all, bg="#555", fg="white"
        ).grid(row=0, column=10, padx=5)
        tk.Button(
            top,
            text="Compare All",
            command=self.compare_algorithms,
            bg="#222",
            fg="orange",
        ).grid(row=0, column=11, padx=5)
        tk.Button(
            top,
            text="Load Demo",
            command=self.load_demo_inputs,
            bg="#444",
            fg="white",
        ).grid(row=0, column=12, padx=5)

        # ---------- Info Box (Right Side) ----------
        inner_frame = tk.Frame(
            top,
            bg="#111",
            bd=2,
            relief="ridge",
            highlightbackground="#000dff",
            highlightthickness=3,
            width=290,
            height=180,
        )
        inner_frame.grid(row=0, column=13, padx=20, pady=5, sticky="ns")
        inner_frame.grid_propagate(False)  # Fix size

        # ---------- Info text inside box ----------
        info_text = (
            "➤ Arrival Time: 0 for all processes\n"
            "\n"
            "➤ Time Quantum: 2 units\n"
            "   (applied only to Round Robin scheduling)\n"
        )
        info_label = tk.Label(
            inner_frame,
            text=info_text,
            fg="#fefefe",
            bg="#111",
            justify="left",
            font=("Orbitron", 14, "bold"),
            padx=25,
            pady=25,
            wraplength=300,
        )
        info_label.grid(row=0, column=0, sticky="nsew")
        inner_frame.grid_rowconfigure(0, weight=1)
        inner_frame.grid_columnconfigure(0, weight=1)

        # ----------  Hover Glow Effect ----------
        def on_enter(e):
            inner_frame.config(highlightthickness=5)
            info_label.config(bg="#1a1a1a")

        def on_leave(e):
            inner_frame.config(highlightthickness=3)
            info_label.config(bg="#111")

        inner_frame.bind("<Enter>", on_enter)
        inner_frame.bind("<Leave>", on_leave)

        # ---------- Semaphore Status Label ----------
        self.sem_label = tk.Label(
            root,
            text="Semaphore: UNLOCKED",
            bg="blue",
            fg="white",
            font=("Arial", 14, "bold"),
        )
        self.sem_label.pack(pady=5, fill="x")

        # ---------- Log Output ----------
        self.log_text = tk.Text(root, height=6, bg="#111", fg="#ccc")  # Log area
        self.log_text.pack(fill="x", padx=10, pady=5)  # Display event logs

        # ---------- Results Table ----------
        columns = (
            "PID",
            "Arrival",
            "Burst",
            "Start",
            "Completion",
            "Waiting",
            "Turnaround",
        )
        self.table = ttk.Treeview(root, columns=columns, show="headings", height=6)
        for col in columns:
            self.table.heading(col, text=col)  # Set column header
            self.table.column(col, width=90)  # Fixed width
        self.table.pack(padx=10, pady=5)

        # ---------- Chart Frame ----------
        self.chart_frame = tk.Frame(root, bg="#1e1e1e")
        self.chart_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # ---------- Average Waiting & Turnaround Label ----------
        self.avg_label = tk.Label(
            root, text="", bg="#1e1e1e", fg="white", font=("Arial", 11)
        )
        self.avg_label.pack(pady=5)

        # ---------- CPU Metrics Label ----------
        self.cpu_metrics_label = tk.Label(
            root, text="", bg="#1e1e1e", fg="white", font=("Arial", 11, "bold")
        )
        self.cpu_metrics_label.pack(pady=5)  # Show CPU utilisation & throughput

    # -------------------- Demo Input Loader --------------------
    def load_demo_inputs(self):
        """Load example processes for testing."""

        self.clear_all()  # Clear previous data
        demo_bursts = [5, 3, 8, 6]
        for b in demo_bursts:
            self.burst_entry.delete(0, "end")  # Clear entry
            self.burst_entry.insert(0, str(b))  # Insert burst
            self.add_process()  # Add process
        self._log_event("Demo processes loaded successfully!")

    # -------------------- Quantum Toggle --------------------
    def _toggle_quantum(self, event=None):
        self.quantum_entry.config(state="disabled")  # Always disabled, fixed at 2

    # -------------------- Semaphore Handling --------------------
    def _update_semaphore(self, state, pid=None):
        """Update semaphore label safely in GUI thread."""

        def update_label():
            if state == "LOCKED":
                self.sem_label.configure(text=f"Semaphore: LOCKED by P{pid}", bg="red")
            else:
                self.sem_label.configure(text="Semaphore: UNLOCKED", bg="blue")

        self.root.after(0, update_label)  # Thread-safe update

    # -------------------- Logging --------------------
    def _log_event(self, text):
        """Insert log message safely in GUI thread."""

        def insert_text():
            self.log_text.insert("end", f"{text}\n")  # Add log line
            self.log_text.see("end")  # Scroll to latest

        self.root.after(0, insert_text)  # Thread-safe

    # -------------------- Add & Clear Processes --------------------
    def add_process(self):
        """Add new process with fixed arrival and user burst."""

        try:
            arr = 0  # Fixed arrival
            burst = int(self.burst_entry.get())  # Get burst input
        except ValueError:
            self._log_event(
                "⚠ Invalid input: Burst Time must be a positive integer."
            )  # Invalid number
            return

        p = Process(self.pid_counter, arr, burst)  # Create process
        self.processes.append(p)
        self.pid_counter += 1  # Increment PID
        self._log_event(f"Added P{p.pid}: Arrival={p.arrival}, Burst={p.burst}")

    def clear_all(self):
        """Reset all processes, logs, table, and charts."""

        self.processes.clear()  # Remove all processes
        self.pid_counter = 1
        self.table.delete(*self.table.get_children())  # Clear table
        self.avg_label.config(text="")  # Reset avg label
        self.log_text.delete("1.0", "end")  # Clear logs
        for w in self.chart_frame.winfo_children():  # Remove charts
            w.destroy()
        self._update_semaphore("UNLOCKED")  # Reset semaphore
        self._log_event("Cleared all processes.")

    # -------------------- Run Algorithm --------------------
    def run_algorithm(self):
        """Run selected scheduling algorithm in separate thread."""
        threading.Thread(target=self._run_algorithm_thread, daemon=True).start()

    def _run_algorithm_thread(self):
        """Internal method to execute algorithm and update GUI."""
        algo = self.alg_option.get()  # Get selected algorithm

        # Queue initial log
        self.threaded_events.append(lambda: self._log_event(f"▶ Running {algo}..."))

        if algo == "FCFS":
            completed = self.fcfs(simulate=True)  # Run FCFS
        elif algo == "SJF":
            completed = self.sjf(simulate=True)  # Run SJF
        else:
            q = 2
            completed = self.round_robin(q, simulate=True)  # Run RR

        # Execute queued GUI updates safely in main thread
        for event in self.threaded_events:
            self.root.after(0, event)
        self.threaded_events.clear()

        # Display results
        self.root.after(0, lambda: self._display_results(completed))

    # -------------------- Algorithms --------------------
    def fcfs(self, simulate=True):
        """First-Come-First-Serve scheduling."""
        plist = sorted(self.processes, key=lambda p: p.arrival)  # Sort by arrival
        time = 0
        result = []

        for p in plist:
            if time < p.arrival:
                time = p.arrival  # Wait for process if CPU idle

            if simulate:
                self._update_semaphore_threadsafe("LOCKED", p.pid)  # Lock semaphore
                self._log_event_threadsafe(f"P{p.pid} executing...")  # Log start

            # Set timings
            p.start = time
            p.completion = time + p.burst
            p.waiting = p.start - p.arrival
            p.turnaround = p.completion - p.arrival
            time += p.burst

            if simulate:
                self._update_semaphore_threadsafe("UNLOCKED")  # Release semaphore
                self._log_event_threadsafe(f"P{p.pid} completed.")  # Log completion

            result.append(p)

        return result

    def sjf(self, simulate=True):
        """Shortest Job First scheduling (non-preemptive)."""
        plist = sorted(
            self.processes, key=lambda p: (p.arrival, p.burst)
        )  # Sort arrival & burst
        completed, time, ready = [], 0, []

        while plist or ready:
            # Add processes that have arrived to ready queue
            ready += [p for p in plist if p.arrival <= time]
            plist = [p for p in plist if p.arrival > time]
            if not ready:
                time += 1  # CPU idle
                continue

            p = min(ready, key=lambda x: x.burst)  # Pick shortest burst
            ready.remove(p)

            if simulate:
                self._update_semaphore_threadsafe(
                    "LOCKED", p.pid
                )  # Mark process as locked
                self._log_event_threadsafe(
                    f"P{p.pid} executing..."
                )  # Log process execution

            # Set timings
            p.start = time
            p.completion = time + p.burst
            p.waiting = p.start - p.arrival
            p.turnaround = p.completion - p.arrival
            time += p.burst

            if simulate:
                self._update_semaphore_threadsafe(
                    "UNLOCKED"
                )  # Mark process as unlocked
                self._log_event_threadsafe(
                    f"P{p.pid} completed."
                )  # Log process completion

            completed.append(p)

        return completed

    def round_robin(self, quantum, simulate=True):
        """Round Robin scheduling with fixed quantum."""
        plist = sorted(self.processes, key=lambda p: p.arrival)  # Sort by arrival
        time = 0  # Initialize simulation time
        queue = []  # ready queue
        result = []  # execution order
        finished = set()  # finished processes
        remaining = {p.pid: p.burst for p in plist}  # Track remaining burst
        started = {}  # start times

        while len(finished) < len(plist):
            # Add newly arrived processes to queue
            for p in plist:
                if p.arrival <= time and p.pid not in queue and p.pid not in finished:
                    queue.append(p.pid)
            if not queue:
                time += 1  # CPU idle
                continue

            pid = queue.pop(0)  # Get next process ID from queue
            p = next(x for x in plist if x.pid == pid)  # Retrieve process object by ID

            if pid not in started:
                p.start = time  # First start time
                started[pid] = True

            run_time = min(quantum, remaining[pid])  # Compute time slice

            if simulate:
                self._update_semaphore_threadsafe("LOCKED", p.pid)  # Lock process
                self._log_event_threadsafe(
                    f"P{p.pid} running for {run_time} unit(s)."
                )  # Log process running

            p.slices.append((time, run_time))  # Track slice
            time += run_time
            remaining[pid] -= run_time

            # Enqueue newly arrived processes
            for proc in plist:
                if (
                    proc.arrival <= time
                    and proc.pid not in queue
                    and proc.pid not in finished
                    and proc.pid != pid
                ):
                    queue.append(proc.pid)

            if remaining[pid] == 0:  # Process finished
                # Record process completion and metrics
                p.completion = time
                p.turnaround = p.completion - p.arrival
                p.waiting = p.turnaround - p.burst
                # Mark process as finished and add to results
                finished.add(pid)
                result.append(p)
                if simulate:
                    self._update_semaphore_threadsafe("UNLOCKED")  # Unlock process
                    self._log_event_threadsafe(
                        f"P{p.pid} finished."
                    )  # Log process finished
            else:  # Process paused, re-queue
                queue.append(pid)
                if simulate:
                    self._update_semaphore_threadsafe("UNLOCKED")  # Unlock process
                    self._log_event_threadsafe(
                        f"P{p.pid} paused, remaining {remaining[pid]} unit(s)."  # Log process paused
                    )

        return result

    # -------------------- Display Results --------------------
    def _display_results(self, completed: List[Process]):
        """Update table, metrics, and chart with completed process info."""

        # Clear previous table rows
        for r in self.table.get_children():
            self.table.delete(r)

        # Insert completed processes into table
        for p in completed:
            self.table.insert(
                "",
                "end",
                values=(
                    p.pid,
                    p.arrival,
                    p.burst,
                    p.start,
                    p.completion,
                    p.waiting,
                    p.turnaround,
                ),
            )

        # Compute average waiting & turnaround times
        avg_wait = sum(p.waiting for p in completed) / len(completed)
        avg_turn = sum(p.turnaround for p in completed) / len(completed)
        self.avg_label.config(
            text=f"Average Waiting Time = {avg_wait:.2f}, Average Turnaround Time = {avg_turn:.2f}"
        )

        # ---------- CPU Metrics ----------
        total_time = max(p.completion for p in completed) - min(
            p.arrival for p in completed
        )
        total_burst = sum(p.burst for p in completed)
        cpu_util = (total_burst / total_time) * 100  # CPU Utilisation %
        throughput = len(completed) / total_time  # Processes per unit time
        idle_time = total_time - total_burst  # CPU Idle time units

        # Update the CPU metrics label
        self.cpu_metrics_label.config(
            text=(
                f"CPU Utilisation: {cpu_util:.2f}% | "
                f"Throughput: {throughput:.2f} processes/unit time | "
                f"CPU Idle Time: {idle_time} units"
            )
        )

        # Draw Gantt chart
        self._draw_chart(completed)

    # -------------------- Draw Gantt Chart --------------------
    def _draw_chart(self, completed: List[Process]):
        """Draw Gantt chart for completed processes."""

        # Clear previous chart
        for w in self.chart_frame.winfo_children():
            w.destroy()

        fig, ax = plt.subplots(figsize=(8, 2))
        y = 10
        colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]  # Colour palette

        for p in completed:
            if p.slices:  # Round Robin: draw multiple slices
                for start, duration in p.slices:
                    ax.barh(
                        y,
                        duration,
                        left=start,
                        height=0.4,
                        color=colors[(p.pid - 1) % 4],
                    )
                    ax.text(
                        start + duration / 2,
                        y,
                        f"P{p.pid}",
                        ha="center",
                        va="center",
                        color="white",
                    )
            else:  # FCFS/SJF: single continuous block
                ax.barh(
                    y, p.burst, left=p.start, height=0.4, color=colors[(p.pid - 1) % 4]
                )
                ax.text(
                    p.start + p.burst / 2,
                    y,
                    f"P{p.pid}",
                    ha="center",
                    va="center",
                    color="white",
                )

        ax.set_xlabel("Time")
        ax.set_yticks([])
        ax.legend(loc="upper center", ncol=len(completed))

        # Set chart title
        algo = self.alg_option.get()
        if algo == "Round Robin":
            q = 2
            ax.set_title(
                f"{algo} Scheduling (Quantum = {q})",
                fontsize=12,
                color="orange",
                pad=25,
            )
        else:
            ax.set_title(f"{algo} Scheduling", fontsize=12, color="orange", pad=25)

        plt.tight_layout()

        # Embed matplotlib chart in Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # -------------------- Compare All Algorithms --------------------
    def compare_algorithms(self):
        """Run all scheduling algorithms and compare average waiting & turnaround times."""

        if not self.processes:
            self._log_event(" Add processes before comparing.")
            return

        # Backup original processes
        original = [
            Process(p.pid, p.arrival, p.burst, slices=[]) for p in self.processes
        ]

        # Run algorithms without simulation (no waiting/logging)
        fcfs_result = self.fcfs(simulate=False)
        self.processes = [
            Process(p.pid, p.arrival, p.burst, slices=[]) for p in original
        ]

        sjf_result = self.sjf(simulate=False)
        self.processes = [
            Process(p.pid, p.arrival, p.burst, slices=[]) for p in original
        ]

        rr_result = self.round_robin(2, simulate=False)
        self.processes = [
            Process(p.pid, p.arrival, p.burst, slices=[]) for p in original
        ]

        # Compute average metrics
        results = {
            "FCFS": (
                sum(p.waiting for p in fcfs_result) / len(fcfs_result),
                sum(p.turnaround for p in fcfs_result) / len(fcfs_result),
            ),
            "SJF": (
                sum(p.waiting for p in sjf_result) / len(sjf_result),
                sum(p.turnaround for p in sjf_result) / len(sjf_result),
            ),
            "RR (q=2)": (
                sum(p.waiting for p in rr_result) / len(rr_result),
                sum(p.turnaround for p in rr_result) / len(rr_result),
            ),
        }

        # Draw chart immediately
        self._draw_comparison_chart(results)
        self._log_event(" Comparison complete.")

    def _draw_comparison_chart(self, results):
        """Draw a bar chart comparing average waiting and turnaround times for all algorithms."""

        # Clear previous chart
        for w in self.chart_frame.winfo_children():
            w.destroy()

        fig, ax = plt.subplots(figsize=(6, 3))
        algos = list(results.keys())
        waits = [results[a][0] for a in algos]
        turns = [results[a][1] for a in algos]
        x = range(len(algos))

        # Draw bars for waiting and turnaround times
        ax.bar(
            x,
            waits,
            width=0.4,
            label="Average Waiting Time",
            align="center",
            color="#ff7f0e",
        )
        ax.bar(
            [i + 0.4 for i in x],
            turns,
            width=0.4,
            label="Average Turnaround Time",
            align="center",
            color="#1f77b4",
        )

        ax.set_xticks([i + 0.2 for i in x])
        ax.set_xticklabels(algos)
        ax.set_ylabel("Time (units)")
        ax.set_title("Algorithm Performance Comparison", color="orange")
        ax.legend()
        plt.tight_layout()

        # Embed chart in Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # -------------------- Thread-safe GUI helpers --------------------
    def _log_event_threadsafe(self, text):
        """Add log events to queue to run safely in main thread"""
        self.threaded_events.append(lambda: self._log_event(text))

    def _update_semaphore_threadsafe(self, state, pid=None):
        """Add semaphore updates to queue to run safely in main thread"""
        self.threaded_events.append(lambda: self._update_semaphore(state, pid))


# -------------------- Run the App --------------------
if __name__ == "__main__":
    root = tk.Tk()

    # ---------- Global Styling ----------
    root.configure(bg="#0a0a0f")
    root.option_add("*Font", "Orbitron 12")
    root.option_add("*Foreground", "#e8f6ff")
    root.option_add("*Background", "#0a0a0f")
    root.option_add("*Button.Background", "#14141f")
    root.option_add("*Button.Foreground", "#d0f7ff")
    root.option_add("*Entry.Background", "#161621")
    root.option_add("*Entry.Foreground", "#cbe8ff")
    root.option_add("*Label.Background", "#0a0a0f")
    root.tk.call("tk", "scaling", 1.25)

    # ---------- Futuristic Glass Panel ----------
    glass_panel = tk.Frame(
        root,
        bg="#11121a",
        highlightthickness=2,
        highlightbackground="#00d4ff",
        width=1000,
        height=600,
    )
    glass_panel.place(relx=0.5, rely=0.5, anchor="center")

    # ---------- Soft pulsing glow animation ----------
    def pulse_glow():
        colors = ["#00d4ff", "#0094ff", "#005fff", "#0094ff"]
        i = 0

        def step():
            nonlocal i
            glass_panel.config(highlightbackground=colors[i])
            i = (i + 1) % len(colors)
            root.after(180, step)

        step()

    pulse_glow()

    # ---------- Initialize Scheduler App ----------
    app = SchedulerApp(root)
    root.mainloop()
