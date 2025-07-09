# mixed_in_json_out.py
import json

def mixed_in_direct_out(p3, _input_files):
    with open(_input_files["json"]) as json_data:
        inputs = json.load(json_data)
    p4 = inputs["p4"]
    p5 = p3 + p4

    print(f"{p3=}")
    print(f"{p4=}")
    print(f"{p5=}")

    return {"p5": p5}
