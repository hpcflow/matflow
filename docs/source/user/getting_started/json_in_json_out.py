# json_in_json_out.py
import json

def json_in_json_out(_input_files, _output_files):
    with open(_input_files["json"]) as json_data:
        inputs = json.load(json_data)
    p1 = inputs["p1"]
    p2 = inputs["p2"]

    p3 = p1 + p2
    with open(_output_files["json"], 'w') as f:
        json.dump({"p3": p3}, f)
