# json_in_direct_out.py
import json

def json_in_direct_out(_input_files):
    with open(_input_files["json"]) as json_data:
        inputs = json.load(json_data)
    p3 = inputs["p3"]
    p4 = p3 + 1

    print(f"{p3=}")
    print(f"{p4=}")

    return {"p4": p4}
