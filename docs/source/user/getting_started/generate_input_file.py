# generate_input_file.py
import json

def generate_input_file(path: str, input_data: list):
    """Generate an input file"""
    with open(path, "w") as f:
        json.dump(input_data, f, indent=2)
