from __future__ import annotations

from matflow.param_classes.moose import MooseInputDeck


def write_input(
    path,
    input_deck: MooseInputDeck | None = None,
    input_deck_variables=None,
    elasticity=None,
    _exodus_generation_input_deck: MooseInputDeck | None = None,
):

    if _exodus_generation_input_deck is not None:
        # this is just for generating an Exodus file from a Gmsh .msh file
        # for easier visualisation:
        input_deck = _exodus_generation_input_deck

    if not isinstance(input_deck, MooseInputDeck):
        input_deck = MooseInputDeck(**input_deck)

    if input_deck_variables:
        input_deck.add_variables(input_deck_variables)
    if elasticity:
        input_deck.update(
            {("Materials", "elasticity", k): v for k, v in elasticity.items()}
        )
    input_deck.to_file(path)
