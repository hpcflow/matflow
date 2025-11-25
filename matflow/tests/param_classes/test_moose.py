from textwrap import dedent

from matflow.param_classes.moose import MooseInputDeck


def test_round_trip_no_comments():
    string = dedent(
        """\
        [Mesh]
            [generated]
                type = GeneratedMeshGenerator
                dim = 2
                nx = 10
                ny = 5
                xmax = 0.1
                ymax = 0.05
                elem_type = QUAD4
            []
        []
        [Variables]
            [temperature]
                initial_condition = 20.0
            []
        []
        [Kernels]
            [heat_conduction]
                type = HeatConduction
                variable = temperature
            []
        []
        [Materials]
            [copper_thermal]
                type = HeatConductionMaterial
                thermal_conductivity = 384.0
                specific_heat = 406.0
            []
            [copper_density]
                type = GenericConstantMaterial
                prop_names = density
                prop_values = 8829.0
            []
        []
        [BCs]
            [heat_flux_out]
                type = ConvectiveHeatFluxBC
                variable = temperature
                boundary = left
                T_infinity = 20.0
                heat_transfer_coefficient = 125000.0
            []
            [heat_flux_in]
                type = NeumannBC
                variable = temperature
                boundary = right
                value = 500000.0
            []
        []
        [Executioner]
            type = Steady
        []
        [Postprocessors]
            [max_temp]
                type = NodalExtremeValue
                variable = temperature
            []
            [avg_temp]
                type = AverageNodalVariableValue
                variable = temperature
            []
        []
        [Outputs]
            exodus = True
        []
    """
    )
    inp = MooseInputDeck.from_string(string)
    assert inp.block_dat["Variables"]["temperature"]["initial_condition"] == "20.0"
    assert inp.block_dat["Postprocessors"]["max_temp"]["variable"] == "temperature"
    assert inp.to_string() == string
