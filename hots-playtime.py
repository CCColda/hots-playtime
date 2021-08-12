from subprocess import CalledProcessError, run
from pprint import pprint
from os import environ
from pathlib import Path
from json import dumps
from math import floor
from datetime import datetime
from signal import signal, SIGINT
import sys
import asyncio

async def parse_info(file, playerName):
    try:
        process_header = run([sys.executable, "-m", "heroprotocol", "--header", file],
                            capture_output=True,
                            check=True)

        process_details = run([sys.executable, "-m", "heroprotocol", "--details", file],
                            capture_output=True,
                            check=True)

        output_header = process_header.stdout.decode("utf-8")
        output_details = process_details.stdout.decode("utf-8")
        """ output_header = "{}"
        output_details = "{}" """

        if not output_header or not output_details:
            return {
                'duration': 0,
                'hero': "Unknown"
            }

        dict_header = eval(output_header)
        dict_details = eval(output_details)

        player_hero_array = [player['m_hero'].decode('utf-8') for player in dict_details['m_playerList'] if player['m_name'].decode('utf-8').strip() == playerName.strip()]

        return {
            'duration': dict_header['m_elapsedGameLoops'] / 8,
            'hero': player_hero_array[0] if len(player_hero_array) > 0 else "Unknown"
        }
    except CalledProcessError as exc:
        print(f"Called process failed in parse_info - {str(exc)}")
        return {
            'duration': 0,
            'hero': "Unknown"
        }
    except BaseException as exc:
        print(f"Exception raised in parse_info: {exc}")
        return {
            'duration': 0,
            'hero': "Unknown"
        }

def get_statistic(array):
    heroes_dict = {}
    time_sum = 0

    for parsed_dict in array:
        time_sum += parsed_dict['duration']
        if parsed_dict['hero'] in heroes_dict:
            heroes_dict[parsed_dict['hero']] += parsed_dict['duration']
        else:
            heroes_dict.update({parsed_dict['hero']: parsed_dict['duration']})

    return {
        'heroes': heroes_dict,
        'duration': time_sum,
        'matches': len(array)
    }

def check_heroprotocol():
    try:
        run([sys.executable, "-m", "heroprotocol", "-h"], capture_output=True, check=True)
        return True
    except CalledProcessError:
        return False

async def main(argv):
    signal(SIGINT, lambda _sig, _frame: exit(128))

    if not check_heroprotocol():
        print("Dependency \"heroprotocol\" not found. Please install it according to README.md.")
        return 1

    num_sets = 50

    usage = ("Heroes of the Storm playtime - v1.0\n\nUsage:\n"
        f"\"{sys.executable}\" \"{argv[0]}\" <player name> [replay root folder] [output file]")

    files = []
    out_file = f"hots-playtime-{datetime.now().isoformat().split('T')[0]}.json"
    player = ""

    if len(argv) >= 2:
        player = argv[1]
    else:
        print(usage)
        print("Please provide a player name.")
        return 2

    if len(argv) >= 3:
        files=list(Path(argv[2]).glob("**/*.StormReplay"))
    else:
        if sys.platform == "win32":
            files = list(Path(environ["USERPROFILE"]).glob(
                "Documents/Heroes of the Storm/Accounts/*/*/Replays/**/*.StormReplay"))
        elif sys.platform == "darwin":
            files = list(Path("~").glob("Library/Application Support/Blizzard/Heroes of the Storm/Accounts/*/*/Replays/**/*.StormReplay"))
        else:
            print(usage)
            print(f"Please provide a replay path.")
            return 2
    
    if len(argv) >= 4:
        out_file = argv[3]

    print(f"Globbed {len(files)} files to search")
    print(f"Searching for replays of \"{player}\"")

    print("Processing...")
    promises = [parse_info(file, player) for file in files]

    finished = []

    set_size = floor(len(promises) / num_sets)

    for set_id in range(num_sets):
        print(f"Running set #{set_id} with {set_size} items")

        promise_set = promises[set_id * set_size: (set_id + 1) * set_size]
        finished = finished + await asyncio.gather(*promise_set, return_exceptions=True)

    print(
        f"Running last set with {len(promises) - (num_sets - 1) * set_size} items")
    finished=finished + await asyncio.gather(*promises[num_sets * set_size:])

    print("Summing up...")
    statistic=get_statistic(finished)

    pprint(statistic)

    print(f"Writing result JSON to \"{out_file}\"...")

    with open(out_file, "w") as outfile:
        outfile.write(dumps(statistic))

    return 0

if __name__ == "__main__":
    loop=asyncio.get_event_loop()
    loop.run_until_complete(main(sys.argv))
    loop.close()
