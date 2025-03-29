import argparse
import ctypes
import sys
from time import sleep

from psutil import Process, Popen, process_iter, cpu_count


#Default values
MIN_FREE_PHYSICAL_CORES = 1
ANOMALY_LAUNCHER_FILE = 'AnomalyLauncher.exe'



def arguments_parser() -> argparse.Namespace:
    launcher_file = sys.argv[0]
    arg_parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog=str(launcher_file),
        description=(
           'Executes Anomaly Launcher and removes the CPU affinity of N first cores from the game when it launches.\n' \
           'Warns user if game launches without DirectX 11.'
        )
    )
    arg_parser.add_argument(
        '-m', '--min-free-cpu-cores',
        type=int,
        dest='min_physical_cores',
        required=False,
        default=MIN_FREE_PHYSICAL_CORES,
        action='store',
        help=f'Sets the minimum amount of CPU physical cores reserved to system. (default: {MIN_FREE_PHYSICAL_CORES})'
    )
    arg_parser.add_argument(
        '-l', '--launcher',
        type=str,
        dest='launcher',
        required=False,
        default=ANOMALY_LAUNCHER_FILE,
        action='store',
        help=f'Set the ANOMALY launcher file. If passed None as launcher, do not execute the game launcher and just waits the game process. (default: {ANOMALY_LAUNCHER_FILE})'
    )
    arg_parser.add_argument(
        '-d', '--debug',
        dest='debug',
        required=False,
        action='store_true',
        help='Print game process details and keep console window open after game process termination.'
    )
    return arg_parser.parse_args()


def message_box(title:str, message:str, style:int) -> int:
    """Shows a message box (Windows only)

    Args:
        title (str): Window Title
        message (str): Message
        style (int): Type of message flag (sum the Button flag with Window icon flag):
            Button flags:
            # 0 : OK
            # 1 : OK | Cancel
            # 2 : Abort | Retry | Ignore
            # 3 : Yes | No | Cancel
            # 4 : Yes | No
            # 5 : Retry | No
            # 6 : Cancel | Try Again | Continue

            Window icon flags:
            # 0  : No icon
            # 16 : Stop-sign icon
            # 32 : Question-mark icon
            # 48 : Exclamation-point icon
            # 64 : Information-sign icon consisting of an 'i' in a circle

    Returns:
        int: Button clicked:
            # 1  : Ok
            # 2  : Cancel
            # 3  : Abort
            # 4  : Retry
            # 5  : Ignore
            # 6  : Yes
            # 7  : No
            # 10 : Try Again
            # 11 : Continue
    """
    return ctypes.windll.user32.MessageBoxW(0, message, title, style)


def debugger_print_lock(game_process:Process):
    try:
        n_game_cores = len(game_process.cpu_affinity())
        cpu_total = game_process.cpu_percent()
        game_is_running = game_process.is_running()
    except:
        return
    print('DEBUG: CPU usage (Actual | Max in last 5 minutes):')
    iter_delay = 5 #s
    n_iter_max = ((5 * 60) // iter_delay) - 1 #iter 0 counts
    cpu_total_array = [0.0] * (n_iter_max + 1)
    per_cpu_average_array = [0.0] * (n_iter_max + 1)
    iter_idx = 0
    while game_is_running:
        sleep(iter_delay)
        try:
            game_is_running = game_process.is_running()
            cpu_total = game_process.cpu_percent()
        except:
            break
        per_cpu_average = cpu_total / n_game_cores
        cpu_total_array[iter_idx] = cpu_total
        per_cpu_average_array[iter_idx] = per_cpu_average
        max_cpu_total = max(cpu_total_array)
        max_per_cpu_average = max(per_cpu_average_array)
        iter_idx = 0 if (iter_idx >= n_iter_max) else (iter_idx + 1)
        sys.stdout.write(
            f'\rTotal: {cpu_total:.2f}% {" "*7}' \
            f'Per Core: {per_cpu_average:.2f}% {" "*4}' \
            f'|{" "*4}' \
            f'Max total: {max_cpu_total:.2f}%{" "*7}' \
            f'Max per Core: {max_per_cpu_average:.2f}%     '
        )
        sys.stdout.flush()
    print('\n')


class WelcomeLauncher():
    def __init__(self, min_free_physical_cores:int):
        self.game_exe_list = [
            "AnomalyDX11AVX.exe",
            "AnomalyDX11.exe",
            "AnomalyDX10AVX.exe",
            "AnomalyDX10.exe",
            "AnomalyDX9AVX.exe",
            "AnomalyDX9.exe",
            "AnomalyDX8AVX.exe",
            "AnomalyDX8.exe"
        ]
        self.dx11_game_exe_list = [
            "AnomalyDX11AVX.exe",
            "AnomalyDX11.exe",
        ]

        logical_cores = cpu_count(logical=True)
        physical_cores = cpu_count(logical=False)
        min_free_physical_cores = min(min_free_physical_cores, physical_cores-1)

        if logical_cores == physical_cores:
            self.game_cores = list(range(min_free_physical_cores, physical_cores))
        else:
            self.game_cores = list(range(min_free_physical_cores*2, (logical_cores - physical_cores)*2))

        print(f'{min_free_physical_cores=}\n{physical_cores=}\n{logical_cores=}\ngame_cores={self.game_cores}\n')


    def set_anomaly_affinity(self) -> Process|None:
        for process in filter(
                lambda p: p.name().startswith('Anomaly'),
                process_iter(['pid', 'name'])
            ):
            if process.name() in self.game_exe_list:
                game_process = Process(process.pid)
                game_process.cpu_affinity(self.game_cores)
                print(f'Found game process: {process.name()}\nPID: {process.pid}\n')
                if process.name() not in self.dx11_game_exe_list:
                    message_box(
                        title='Incorrect DirectX Version',
                        message='The game will crash, use DirectX 11!',
                        style=0+16,
                    )
                return game_process
        return None


def main():
    args = arguments_parser()

    print(f'\nGame Launcher: {args.launcher}\n')
    if args.launcher != 'None':
        try:
            launcher_process = Popen([args.launcher])
        except FileNotFoundError:
            message_box(
                title='File not found',
                message=f'Game launcher {args.launcher} not found!',
                style=0+16,
            )
            raise FileNotFoundError(f'Launcher not found: {args.launcher}')
    else:
        launcher_process = None

    anomaly_affinity_setter = WelcomeLauncher(
        min_free_physical_cores=args.min_physical_cores,
    )
    print('Waiting game process...\n')

    game_launcher_running = True
    game_process = None
    while game_launcher_running and (game_process is None):
        game_process = anomaly_affinity_setter.set_anomaly_affinity()
        sleep(3)
        if launcher_process is None:
            continue
        game_launcher_running = launcher_process.poll() is None
        if not game_launcher_running:
            print('Game launcher finished\n')

    if not args.debug:
        print('Script finished!\n')
        if game_process is None:
            return
        exit_delay = 15
        for s in range(exit_delay):
            sys.stdout.write(f'\rExiting in {exit_delay-(s+1):02d} seconds   ')
            sys.stdout.flush()
            sleep(1)
        return

    debugger_print_lock(game_process)
    print('Script finished!\nClose the game before this window')
    input()



if __name__ == '__main__':
    main()
