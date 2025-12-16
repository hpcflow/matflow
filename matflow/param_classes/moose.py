"""
The moose input deck.
"""

from __future__ import annotations
import re

import logging
from pathlib import Path
from typing import Any
from typing_extensions import ClassVar

from hpcflow.sdk.core.parameters import ParameterValue
from hpcflow.sdk.core.utils import set_in_container

logger = logging.getLogger(__name__)


class MooseBlock:
    """A (recursive) moose block within the input deck file."""

    TAB = "    "

    def __init__(
        self,
        name,
        collection,
        root=False,
        variables=None,
        exclude: Sequence[str] | None = None,
    ):
        self.name = name
        self.root = root
        self.attributes = {}
        self.blocks = []
        self.exclude = tuple(exclude or tuple())
        self.variables = {k: v for k, v in (variables or {}).items() if k not in exclude}

        for key, val in collection.items():
            if key in self.exclude:
                continue
            if isinstance(val, dict):
                self.blocks.append(MooseBlock(key, val))
                continue
            self.attributes[key] = val

    def __eq__(self):
        if not isinstance(other, self.__class__):
            return False
        return (
            self.name == other.name
            and self.attributes == other.attributes
            and self.blocks == other.blocks
            and self.variables == other.variables
        )

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


class MooseInputDeck(ParameterValue):
    """Moose input parametrisation.

    Notes
    -----
    We don't attempt to parse value types (e.g. floats, ints); everything stays as a
    string.
    """

    _typ: ClassVar[str] = "input_deck"

    def __init__(self, variables: dict | None = None, **block_dat) -> None:
        self.block_dat = block_dat
        self.variables = variables or {}

    def update(self, upd: dict[str | tuple[str], Any]):
        """Update paths within the input deck with the specified values."""
        for path, val in upd.items():
            if isinstance(path, str):
                path_t = tuple(path.split("."))
            else:
                path_t = path
            set_in_container(cont=self.block_dat, path=path_t, value=val)

    def add_variables(self, vars):
        """Add variables to the input deck."""
        self.variables.update(vars)

    def to_string(self):
        """Transform to a string."""
        block = MooseBlock(
            "root",
            self.block_dat,
            root=True,
            variables=self.variables,
            exclude=("__comments__",),
        )
        return str(block)

    def to_file(self, path: str | Path):
        """Write the input file to disk."""
        Path(path).write_text(self.to_string(), newline="\n")

    @staticmethod
    def parse_from_string(contents: str) -> tuple[dict[str, Any], dict[str, Any]]:
        """Parse the contents of a MOOSE input deck file, returning the both the nested
        block structure, and any top-level variables."""

        variables = {}
        root = {}
        stack = [(None, root)]  # (block_name, dict)

        # patterns for [BlockName], [] (end), or key = value lines
        block_start = re.compile(r"^\[(.*?)\]$")
        assignment = re.compile(r"^(\w+)\s*=\s*(.+)$")

        for line in contents.splitlines():
            line = line.strip()
            if not line:
                continue

            # extract comments
            comment = None
            if "#" in line:
                line, comment = line.split("#", 1)
                line = line.rstrip()
                comment = comment.strip()

            # store full line comments
            if line == "" and comment:
                # Store comment in the current block
                block_dict = stack[-1][1]
                block_dict.setdefault("__comments__", []).append(comment)
                continue

            look_for_vars = len(stack) == 1

            # block end:
            if line == "[]":
                stack.pop()
                continue

            # block start
            blk_match = block_start.match(line)
            if blk_match:
                name = blk_match.group(1).strip()
                new_dict = {}
                _, parent_dict = stack[-1]

                # insert into parent dict:
                parent_dict[name] = new_dict

                # inline comments
                if comment:
                    new_dict.setdefault("__comments__", []).append(comment)

                # Push to stack
                stack.append((name, new_dict))
                continue

            # assign values:
            assign_match = assignment.match(line)
            if assign_match:
                key, value = assign_match.group(1), assign_match.group(2).strip()
                if look_for_vars:
                    block_dict = variables
                else:
                    block_dict = stack[-1][1]

                block_dict[key] = value
                if comment:
                    block_dict.setdefault("__comments__", []).append(f"{key}: {comment}")
                continue

            raise ValueError(f"Unrecognized line format: {line!r}.")

        return root, variables

    @classmethod
    def from_string(cls, string, updates: dict[str | tuple[str], Any] | None = None):
        """Generate from a string, like that found in a file."""
        block_dat, variables = cls.parse_from_string(string)
        obj = cls(variables=variables, **block_dat)
        if updates:
            obj.update(updates)
        return obj

    @classmethod
    def from_file(
        cls, path: Path | str, updates: dict[str | tuple[str], Any] | None = None
    ):
        """Generate from an existing input file, optionally with updates to the specified
        paths."""
        return cls.from_string(Path(path).read_text(), updates=updates)
