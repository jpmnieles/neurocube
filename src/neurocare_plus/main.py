import sys
import multiprocessing as mp

from models import ModelManager
from views import MainView
from presenter import UiPresenter
from processes import eeg_process, emotibit_process


def main(is_demo=True):
    
    # Initialization
    mp.freeze_support()  # To prevent error when building windows app

    # Multiprocessing Queue Initializations
    cmd_mp_queues = {
        "EEG": mp.Queue(),
        "EMOTIBIT": mp.Queue()
    }
    status_mp_queue = mp.Queue()

    # Multiprocessing Workers Initializations
    workers = {
        "EEG": mp.Process(
            target=eeg_process, 
            args=(cmd_mp_queues["EEG"], status_mp_queue, is_demo),
            daemon=True
        ),
        "EMOTIBIT": mp.Process(
            target=emotibit_process, 
            args=(cmd_mp_queues["EMOTIBIT"], status_mp_queue, is_demo),
            daemon=True
        )
    }

    # Start Worker Processes
    for p_name, process in workers.items():
        process.start()

    # Initialize the GUI
    model_manager = ModelManager()
    main_view = MainView()
    ui_presenter = UiPresenter(model_manager, main_view,
                               cmd_mp_queues, status_mp_queue,
                               model_manager.ctrl_queues, model_manager.display_queues)
    ui_presenter.setup()

    ### Main Loop and Shutdown ###
    try:
        ui_presenter.run()

    except KeyboardInterrupt:
        print("Exit request acknowledged.")
    
    except Exception as e:
        print(f"Unexpected error: {e}")
    
    finally:
        # Shutdown Process
        print("Initiating Graceful Shutdown...")
        
        # Send EXIT Command to All Processes
        for q_name, mp_queue in cmd_mp_queues.items():
            print(f"Sending EXIT command to [{q_name}] process")
            try:
                mp_queue.put({"target": q_name, "action": "EXIT", "payload": None})
            except Exception:
                pass # Happens when command queue is already closed
        
        # Terminate Forcefully All Processes
        for p_name, process in workers.items():
            process.join(timeout=1.0)
            if process.is_alive():
                print(f"Process [{p_name}] hung. Terminating forcefully.")
                process.terminate()
                process.join()
            else:
                print(f"Process [{p_name}] closed cleanly.")

        # Close All Multiprocessing Queues
        for q in cmd_mp_queues.values():
            q.close()
            q.join_thread()
        status_mp_queue.close()
        status_mp_queue.join_thread()

        # Close All Threads
        model_manager.close()

        # System Exit
        print("Shutdown complete. Exiting.")
        sys.exit(0)

if __name__ == "__main__":
    main(is_demo=True)