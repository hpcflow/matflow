import json

def parse_output(my_input_file: str, processed_file: str):
    """Do some post-processing of data files.

    In this instance, we're just making a dictionary containing both the input
    and output data.
    """
    with open(my_input_file, "r") as f:
        input_data = json.load(f)
    with open(processed_file, "r") as f:
        processed_data = json.load(f)

    combined_data = {"input_data": input_data, "output_data": processed_data}
    # Save file so we can look at the data
    with open("parsed_output.json", "w") as f:
        json.dump(combined_data, f, indent=2)

    return {"parsed_output": combined_data}
