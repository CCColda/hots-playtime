# HotS-Playtime
Python script for counting all the playtime spent _(in seconds)_ in Heroes of the Storm, all together, and per hero.

## Usage
```sh
# Usage: python hots-playtime.py <player name> <path to replays> <path to output json>

python hots-playtime.py CoolUsername "path/to/replay/account" "path/to/output/json"
```

## Dependencies
[Heroprotocol](https://github.com/Blizzard/heroprotocol) needs to be set up in the environment for this script to function.

```sh
python -m pip install --upgrade heroprotocol
```

---

Requires [Python 3.8.2](https://www.python.org/downloads/release/python-382/)
