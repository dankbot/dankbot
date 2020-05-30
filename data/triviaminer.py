import requests
import json


def fetch_trivia(trivia_list):
    r = requests.get('https://opentdb.com/api.php?amount=50')
    if r.status_code != 200:
        return False
    j = r.json()
    if j["response_code"] != 0:
        return False
    total_mined = 0
    for t in j["results"]:
        ts = json.dumps(t)
        if ts in trivia_list:
            continue
        total_mined += 1
        trivia_list[ts] = t
    print(f"Mined {total_mined} trivia in this iteration")



with open("trivia.json") as f:
    trivia_list = {json.dumps(v): v for v in json.load(f)}

for i in range(50):
    fetch_trivia(trivia_list)

with open("trivia.json", "w") as f:
    json.dump(list(trivia_list.values()), f)
