import sys
import multiprocessing as mp

from models import ModelManager
from views import MainView
from presenter import UiPresenter
from processes import eeg_process, emotibit_process

# 1. Create a Process Manager to handle on-demand creation
class ProcessManager:
    def __init__(self, cmd_queues, status_queue, is_demo):
        self.cmd_queues = cmd_queues
        self.status_queue = status_queue
        self.is_demo = is_demo
        self.active_workers = {}

    def start_process(self, name):
        """Starts a process dynamically by name."""
        # Prevent starting if it's already running
        if name in self.active_workers and self.active_workers[name].is_alive():
            print(f"Process {name} is already running.")
            return

        print(f"Spinning up {name} process...")
        if name == "EEG":
            p = mp.Process(
                target=eeg_process, 
                args=(self.cmd_queues["EEG"], self.status_queue, self.is_demo),
                daemon=True
            )
        elif name == "EMOTIBIT":
            p = mp.Process(
                target=emotibit_process, 
                args=(self.cmd_queues["EMOTIBIT"], self.status_queue, self.is_demo),
                daemon=True
            )
        else:
            raise ValueError(f"Unknown process name: {name}")

        p.start()
        self.active_workers[name] = p

    def stop_process(self, name):
        """Stops a specific process."""
        if name in self.active_workers and self.active_workers[name].is_alive():
            # Send graceful exit command
            self.cmd_queues[name].put({"target": name, "action": "EXIT", "payload": None})
            
            # Wait for it to close, forcefully terminate if hung
            self.active_workers[name].join(timeout=1.0)
            if self.active_workers[name].is_alive():
                self.active_workers[name].terminate()
                self.active_workers[name].join()
            
            del self.active_workers[name]
            print(f"Process {name} stopped.")

    def stop_all(self):
        """Helper to shut down everything during app exit."""
        for name in list(self.active_workers.keys()):
            self.stop_process(name)


def main(is_demo=True):
    mp.freeze_support()

    # 2. Keep queue initialization in main
    cmd_mp_queues = {
        "EEG": mp.Queue(),
        "EMOTIBIT": mp.Queue()
    }
    status_mp_queue = mp.Queue()

    # 3. Initialize the Process Manager instead of raw workers
    process_manager = ProcessManager(cmd_mp_queues, status_mp_queue, is_demo)

    # 4. Pass the process manager to your presenter
    model_manager = ModelManager()
    main_view = MainView()
    ui_presenter = UiPresenter(
        model_manager, 
        main_view,
        cmd_mp_queues, 
        status_mp_queue,
        model_manager.ctrl_queues, 
        model_manager.display_queues,
        process_manager=process_manager  # <-- Pass it here
    )
    ui_presenter.setup()

    try:
        ui_presenter.run()

    except KeyboardInterrupt:
        print("Exit request acknowledged.")
    
    except Exception as e:
        print(f"Unexpected error: {e}")
    
    finally:
        print("Initiating Graceful Shutdown...")
        
        # 5. Delegate shutdown to the manager
        process_manager.stop_all()

        # Close All Multiprocessing Queues
        for q in cmd_mp_queues.values():
            q.close()
            q.join_thread()
        status_mp_queue.close()
        status_mp_queue.join_thread()

        model_manager.close()
        print("Shutdown complete. Exiting.")
        sys.exit(0)

if __name__ == "__main__":
    main(is_demo=True)