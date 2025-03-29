import argparse
import ctypes
import os.path as osp
import subprocess
from time import sleep

import psutil


#Default values
MIN_FREE_PHYSICAL_CORES = 1
ANOMALY_LAUNCHER_FILE = 'AnomalyLauncher.exe'



def arguments_parser():
    script_file = osp.basename(__file__)
    arg_parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog=f'{script_file}',
        description=(
           'Executes Anomaly Launcher and removes the CPU affinity of N first cores from game when it launches.'
        )
    )

    arg_parser.add_argument(
        '-c', '--min-free-cpu-cores',
        type=int,
        dest='min_physical_cores',
        required=False,
        default=MIN_FREE_PHYSICAL_CORES,
        action='store',
        help=f'Sets the minimum amount of CPU physical cores reserved to system. (default: {MIN_FREE_PHYSICAL_CORES})'
    )

    arg_parser.add_argument(
        '-l', '--launcher',
        dest='launcher',
        required=False,
        default=ANOMALY_LAUNCHER_FILE,
        action='store',
        help=f'Set the ANOMALY launcher file. If passed None as launcher, do not execute the game launcher. (default: {ANOMALY_LAUNCHER_FILE})'
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


class CPU_affinity_setter():
    def __init__(self, min_free_physical_cores:int):
        self.game_exe = [
            "AnomalyDX11AVX.exe",
            "AnomalyDX11.exe",
            "AnomalyDX10AVX.exe",
            "AnomalyDX10.exe",
            "AnomalyDX9AVX.exe",
            "AnomalyDX9.exe",
            "AnomalyDX8AVX.exe",
            "AnomalyDX8.exe"
        ]

        logical_cores = psutil.cpu_count(logical=True)
        physical_cores = psutil.cpu_count(logical=False)
        min_free_physical_cores = min(min_free_physical_cores, physical_cores-1)

        if logical_cores == physical_cores:
            self.game_cores = list(range(min_free_physical_cores, physical_cores))
        else:
            self.game_cores = list(range(min_free_physical_cores*2, (logical_cores - physical_cores)*2))

        print(f'{min_free_physical_cores=}\n{physical_cores=}\n{logical_cores=}\ngame_cores={self.game_cores}\n')


    def set_anomaly_affinity(self) -> int:
        for process in filter(
                lambda p: p.name().startswith('Anomaly'),
                psutil.process_iter(['pid', 'name'])
            ):
            if process.name() in self.game_exe:
                psutil.Process(process.pid).cpu_affinity(self.game_cores)
                print(f'Found game process: {process.name()}\nPID: {process.pid}\n')
                return 0
        return 1


def main():
    args = arguments_parser()

    print(f'\nGame Launcher: {args.launcher}\n')
    if args.launcher != 'None':
        try:
            launcher_process = subprocess.Popen([args.launcher])
        except FileNotFoundError:
            raise FileNotFoundError(f'Launcher not found: {args.launcher}')
    else:
        launcher_process = None

    anomaly_affinity_setter = CPU_affinity_setter(
        min_free_physical_cores=args.min_physical_cores,
    )
    print('Waiting game process...\n')

    game_launcher_open = True
    waiting_game_process = 1
    while game_launcher_open and (waiting_game_process == 1):
        waiting_game_process = anomaly_affinity_setter.set_anomaly_affinity()
        sleep(3)
        if launcher_process is None:
            continue
        game_launcher_open = launcher_process.poll() is None
        if not game_launcher_open:
            print('Game launcher finished\n')



if __name__ == '__main__':
    main()
    input('Press Enter to exit...')
