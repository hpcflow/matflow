from pathlib import Path


class MooseBlock:
    TAB = "    "

    def __init__(self, name, collection, root=False, variables=None, elasticity=None):
        self.name = name
        self.root = root
        self.attributes = {}
        self.blocks = []
        self.variables = variables or {}

        if elasticity and name == "elasticity":

            # TODO: ideally want a "path" rather than "name"
            collection.update(elasticity)
            # print(f"MooseBlock: updating collection: {collection=!r}")

        for key, val in collection.items():
            # if isinstance(val, CommentedMap):
            if isinstance(val, dict):
                self.blocks.append(MooseBlock(key, val, elasticity=elasticity))
                continue
            self.attributes[key] = val

    def __str__(self) -> str:
        if self.root:
            tab = ""
            txt = ""
            for key, val in self.variables.items():
                txt += f"{key} = {val}\n"
        else:
            tab = self.TAB
            txt = f"[{self.name}]\n"

        for key, val in self.attributes.items():
            txt += f"{tab}{key} = {val}\n"
        for block in self.blocks:
            txt += tab
            txt += str(block).replace("\n", f"\n{tab}")
            txt = txt[: len(txt) - len(tab)]
        if not self.root:
            txt += "[]\n"
        return txt

    def to_file(self, path: Path):
        with path.open("wt", newline="\n") as f:
            f.write(self.__str__())


def write_input(path, input_deck, input_deck_variables, elasticity):
    input_deck = MooseBlock(
        "root",
        input_deck,
        root=True,
        variables=input_deck_variables,
        elasticity=elasticity,
    )
    input_deck.to_file(path)
