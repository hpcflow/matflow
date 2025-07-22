# process_input_file.py
import json

def process_input_file():
    """Process an input file.

    This could be a materials science simulation for example.
    """
    with open("input_file.json", "r") as f:
        data = json.load(f)
    data = [item * 2 for item in data]
    with open("processed_file.json", "w") as f:
        json.dump(data, f, indent=2)
