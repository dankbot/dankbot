import re
import asyncio
import platform
import subprocess

P_HIT_CHANCE = re.compile("^Hit Chance: ([0-9.]*)\r?$", re.M)
P_STAND_CHANCE = re.compile("^Stand Chance: ([0-9.]*)\r?$", re.M)


async def run_blahjack(blahjack_path, our_cards, bot_cards, round_no):
    inp = str(len(our_cards)) + " " + " ".join(our_cards) + "\n"
    bot_cards = [c for c in bot_cards if c != "?"]
    inp += str(len(bot_cards)) + " " + " ".join(bot_cards) + "\n"
    inp += str(round_no)
    print(inp)
    if platform.system() == "Windows":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        proc = await asyncio.create_subprocess_exec(blahjack_path, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, startupinfo=startupinfo)
    else:
        proc = await asyncio.create_subprocess_exec(blahjack_path, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE)
    stdout, _ = await proc.communicate(inp.encode())
    stdout = stdout.decode()
    hit_chance = P_HIT_CHANCE.search(stdout)
    stand_chance = P_STAND_CHANCE.search(stdout)
    if not hit_chance or not stand_chance:
        return -1, -1
    return float(hit_chance.group(1)), float(stand_chance.group(1))

