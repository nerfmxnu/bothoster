import os
import subprocess
import threading
import time
import sys

ascii_art = r"""
                                            ,----,
        ,--,    ,----..                   ,/   .`|
      ,--.'|   /   /   \   .--.--.      ,`   .'  :   ,---,.,-.----.
   ,--,  | :  /   .     : /  /    '.  ;    ;     / ,'  .' |\    /  \
,---.'|  : ' .   /   ;.  \  :  /`. /.'___,/    ,',---.'   |;   :    \
|   | : _' |.   ;   /  ` ;  |  |--` |    :     | |   |   .'|   | .\ :
:   : |.'  |;   |  ; \ ; |  :  ;_   ;    |.';  ; :   :  |-,.   : |: |
|   ' '  ; :|   :  | ; | '\  \    `.`----'  |  | :   |  ;/||   |  \ :
'   |  .'. |.   |  ' ' ' : `----.   \   '   :  ; |   :   .'|   : .  /
|   | :  | ''   ;  \; /  | __ \  \  |   |   |  ' |   |  |-,;   | |  \
'   : |  : ; \   \  ',  / /  /`--'  /   '   :  | '   :  ;/||   | ;\  \
|   | '  ,/   ;   :    / '--'.     /    ;   |.'  |   |    \:   ' | \.'
;   : ;--'     \   \ .'    `--'---'     '---'    |   :   .':   : :-'
|   ,/          `---`                            |   | ,'  |   |.'
'---'                                            `----'    `---'
"""

config = {
    "bot_directory": os.path.dirname(os.path.abspath(__file__)),
    "selected_bot": None,
    "action": None
}

processes = {}

def show_help():
    print("\navailable commands:")
    print("  set bot <bot_name>       - select the bot to manage (without .py)")
    print("  set action <action>      - set the action: start, stop, restart")
    print("  show config              - show current configuration")
    print("  show bots                - show available bots")
    print("  show status              - show bot status")
    print("  run                      - execute the action on the selected bot")
    print("  clear                    - clear the screen")
    print("  help                     - show this menu")
    print("  exit                     - exit the program\n")

def show_config():
    print("\ncurrent configuration:")
    print(f"  bot directory: {config['bot_directory']}")
    print(f"  selected bot: {config['selected_bot']}")
    print(f"  action: {config['action']}")
    print("")

def show_bots():
    print("\navailable bots:")
    for file in os.listdir(config["bot_directory"]):
        if file.endswith(".py") and file != os.path.basename(__file__):
            print(f"  - {file[:-3]}")
    print("")

def show_status():
    print("\nbot status:")
    if not processes:
        print("  no bots started.")
    else:
        for bot_name, info in processes.items():
            status = info['status']
            error = info['error']
            if status == 'running':
                print(f"  - {bot_name}: running")
            elif status == 'stopped':
                print(f"  - {bot_name}: stopped")
            elif status == 'errored':
                print(f"  - {bot_name}: errored - {error}")
            else:
                print(f"  - {bot_name}: unknown")
    print("")

def start_bot(bot_name):
    bot_path = os.path.join(config["bot_directory"], f"{bot_name}.py")
    if not os.path.exists(bot_path):
        print(f"\nerror: the bot {bot_name} does not exist.")
        return
    try:
        process = subprocess.Popen([sys.executable, bot_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        processes[bot_name] = {'process': process, 'status': 'running', 'error': None}
        print(f"\nstarted bot: {bot_name}")
    except Exception as e:
        processes[bot_name] = {'process': None, 'status': 'failed', 'error': str(e)}
        print(f"\nerror starting {bot_name}: {e}")

def stop_bot(bot_name):
    if bot_name in processes:
        process = processes[bot_name]['process']
        if process and process.poll() is None:
            process.terminate()
            process.wait()
            processes[bot_name]['manual_stop'] = True
            processes[bot_name]['status'] = 'stopped'
            print(f"\nbot {bot_name} stopped.")
        else:
            print(f"\nbot {bot_name} is not running.")
    else:
        print(f"\nbot {bot_name} has not been started.")

def restart_bot(bot_name):
    print(f"\nrestarting bot {bot_name}...")
    stop_bot(bot_name)
    start_bot(bot_name)

def monitor_bots():
    while True:
        for bot_name, info in list(processes.items()):
            process = info['process']
            if process and process.poll() is not None and not info.get('handled', False):
                return_code = process.returncode
                if info.get('manual_stop', False):
                    info['status'] = 'stopped'
                    print(f"\n{bot_name} terminated.")
                else:
                    if return_code != 0:
                        error = process.stderr.read().decode().strip()
                        info['status'] = 'errored'
                        info['error'] = error
                        print(f"\n{bot_name} terminated with error: {error}")
                    else:
                        info['status'] = 'stopped'
                        print(f"\n{bot_name} terminated.")
                info['handled'] = True
        time.sleep(5)

monitor_thread = threading.Thread(target=monitor_bots, daemon=True)
monitor_thread.start()

def main():
    os.system("cls" if os.name == "nt" else "clear")
    print(ascii_art)

    while True:
        cmd = input("hoster> ").strip().lower()
        parts = cmd.split(" ", 2)

        if len(parts) < 1:
            continue

        command = parts[0]
        args = parts[1:] if len(parts) > 1 else []

        if command == "set":
            if len(args) < 2:
                print("\nusage: set <parameter> <value>")
                continue

            param, value = args[0], args[1]

            if param == "bot":
                config["selected_bot"] = value
                print(f"\nselected bot: {value}")
            elif param == "action":
                if value in ["start", "stop", "restart"]:
                    config["action"] = value
                    print(f"\naction set: {value}")
                else:
                    print("\ninvalid action. use: start, stop, restart")
            else:
                print("\nunknown parameter. use 'help' for commands.")

        elif command == "show":
            if len(args) == 0 or args[0] == "config":
                show_config()
            elif args[0] == "bots":
                show_bots()
            elif args[0] == "status":
                show_status()
            else:
                print("\nusage: show config | show bots | show status")

        elif command == "run":
            if not config["selected_bot"]:
                print("\nerror: you must select a bot with 'set bot <name>'.")
                continue
            if not config["action"]:
                print("\nerror: you must set an action with 'set action <action>'.")
                continue

            if config["action"] == "start":
                start_bot(config["selected_bot"])
            elif config["action"] == "stop":
                stop_bot(config["selected_bot"])
            elif config["action"] == "restart":
                restart_bot(config["selected_bot"])

        elif command == "clear":
            os.system("cls" if os.name == "nt" else "clear")
            print(ascii_art)

        elif command == "help":
            show_help()

        elif command == "exit":
            print("\nclosing the hoster...")
            for bot_name in processes:
                stop_bot(bot_name)
            break

        else:
            print("\nunknown command. use 'help' for available commands.")

if __name__ == "__main__":
    main()
