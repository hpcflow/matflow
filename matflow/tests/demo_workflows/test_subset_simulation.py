import pytest
import matflow as mf


@pytest.mark.integration
def test_subset_sim_toy_model_two_level_external_parameter_flow(
    new_null_config, tmp_path
):

    # use `new_null_config` because currently these workflows include template components
    wk = mf.make_demo_workflow(
        "subset_simulation_toy_model_two_level_external", path=tmp_path
    )

    num_elements = wk.tasks.initialise_markov_chains.num_elements

    for elem_idx in range(num_elements):

        # input of `generate_next_state` from either `initialise_markov_chains`,
        # `increment_chain_inner`, or `increment_chain`:

        init_iters = {
            i.loop_idx["levels"]: i
            for i in wk.tasks.initialise_markov_chains.elements[elem_idx].iterations
        }
        gen_next_iters = {
            (
                i.loop_idx["inner_markov_chain"],
                i.loop_idx["outer_markov_chain"],
                i.loop_idx["levels"],
            ): i
            for i in wk.tasks.generate_next_state.elements[elem_idx].iterations
        }
        inc_chain_inner_iters = {
            (
                i.loop_idx["inner_markov_chain"],
                i.loop_idx["outer_markov_chain"],
                i.loop_idx["levels"],
            ): i
            for i in wk.tasks.increment_chain_inner.elements[elem_idx].iterations
        }
        inc_chain_iters = {
            (i.loop_idx["outer_markov_chain"], i.loop_idx["levels"]): i
            for i in wk.tasks.increment_chain.elements[elem_idx].iterations
        }

        for l_idx, iter_i in gen_next_iters.items():
            if (
                l_idx[0] == 0 and l_idx[1] == 0
            ):  # inner and outer MC loop zeroth iterations
                assert (
                    iter_i.get_data_idx()["inputs.x"]
                    == init_iters[l_idx[2]].get_data_idx()["outputs.x"]
                )

            elif l_idx[0] == 0:  # inner MC loop zeroth iteration, outer MC loop non-zero
                # should be sourced from `increment_chain`
                for lj_idx, iter_j in inc_chain_iters.items():
                    if lj_idx[1] == l_idx[2] and lj_idx[0] == l_idx[1] - 1:
                        assert (
                            iter_i.get_data_idx()["inputs.x"]
                            == iter_j.get_data_idx()["outputs.x"]
                        )

            elif l_idx[0] > 0:  # inner MC loop non-zero iteration:
                # should be sourced from `increment_chain_inner`, previous inner iteration, same outer MC loop iteration
                for lj_idx, iter_j in inc_chain_inner_iters.items():
                    if (
                        lj_idx[2] == l_idx[2]
                        and lj_idx[0] == l_idx[0] - 1
                        and lj_idx[1] == l_idx[1]
                    ):
                        assert (
                            iter_i.get_data_idx()["inputs.x"]
                            == iter_j.get_data_idx()["outputs.x"]
                        )
            else:
                raise RuntimeError(f"no test for loop index: {l_idx}")

        # new state from generate_next_state inner MC used in inner MC system_analysis and increment_chain_inner
        # keys are: (inner_markov_chain, outer_markov_chain, levels)
        gen_next_iters = {
            (
                i.loop_idx["inner_markov_chain"],
                i.loop_idx["outer_markov_chain"],
                i.loop_idx["levels"],
            ): i
            for i in wk.tasks.generate_next_state.elements[elem_idx].iterations
        }
        pre_proc_iters = {
            (
                i.loop_idx["inner_markov_chain"],
                i.loop_idx["outer_markov_chain"],
                i.loop_idx["levels"],
            ): i
            for i in wk.tasks.dummy_pre_processor_2.elements[elem_idx].iterations
        }
        model_iters = {
            (
                i.loop_idx["inner_markov_chain"],
                i.loop_idx["outer_markov_chain"],
                i.loop_idx["levels"],
            ): i
            for i in wk.tasks.model_sum_x_2.elements[elem_idx].iterations
        }
        limit_iters = {
            (
                i.loop_idx["inner_markov_chain"],
                i.loop_idx["outer_markov_chain"],
                i.loop_idx["levels"],
            ): i
            for i in wk.tasks.evaluate_limit_state_normal_sum_2.elements[
                elem_idx
            ].iterations
        }

        # check parameter flow within inner MC chain:

        for l_idx, iter_i in gen_next_iters.items():
            assert (
                pre_proc_iters[l_idx].get_data_idx()["inputs.x"]
                == iter_i.get_data_idx()["outputs.x"]
            )
            assert (
                inc_chain_inner_iters[l_idx].get_data_idx()["inputs.x"]
                == iter_i.get_data_idx()["outputs.x"]
            )

        for l_idx, iter_i in pre_proc_iters.items():
            assert (
                model_iters[l_idx].get_data_idx()["inputs.y"]
                == iter_i.get_data_idx()["outputs.y"]
            )

        for l_idx, iter_i in model_iters.items():
            assert (
                limit_iters[l_idx].get_data_idx()["inputs.sum_y"]
                == iter_i.get_data_idx()["outputs.sum_y"]
            )

        for l_idx, iter_i in limit_iters.items():
            assert (
                inc_chain_inner_iters[l_idx].get_data_idx()["inputs.g"]
                == iter_i.get_data_idx()["outputs.g"]
            )

        # check parameter flow into outer MC chain from inner MC chain:
        # keys are: (outer_markov_chain, levels)

        pre_proc_iters = {
            (i.loop_idx["outer_markov_chain"], i.loop_idx["levels"]): i
            for i in wk.tasks.dummy_pre_processor_3.elements[elem_idx].iterations
        }
        model_iters = {
            (i.loop_idx["outer_markov_chain"], i.loop_idx["levels"]): i
            for i in wk.tasks.model_sum_x_3.elements[elem_idx].iterations
        }
        limit_iters = {
            (i.loop_idx["outer_markov_chain"], i.loop_idx["levels"]): i
            for i in wk.tasks.evaluate_limit_state_normal_sum_3.elements[
                elem_idx
            ].iterations
        }

        # final inner MC chain iterations only:
        inc_chain_inner_max_iters = {}
        max_inner_iter = -1
        for i in wk.tasks.increment_chain_inner.elements[elem_idx].iterations:
            if i.loop_idx["inner_markov_chain"] > max_inner_iter:
                inc_chain_inner_max_iters[
                    (i.loop_idx["outer_markov_chain"], i.loop_idx["levels"])
                ] = i

        for l_idx, iter_i in inc_chain_inner_max_iters.items():
            assert (
                pre_proc_iters[l_idx].get_data_idx()["inputs.x"]
                == iter_i.get_data_idx()["outputs.x"]
            )

        for l_idx, iter_i in pre_proc_iters.items():
            assert (
                model_iters[l_idx].get_data_idx()["inputs.y"]
                == iter_i.get_data_idx()["outputs.y"]
            )

        for l_idx, iter_i in model_iters.items():
            assert (
                limit_iters[l_idx].get_data_idx()["inputs.sum_y"]
                == iter_i.get_data_idx()["outputs.sum_y"]
            )

        for l_idx, iter_i in limit_iters.items():
            assert (
                inc_chain_iters[l_idx].get_data_idx()["inputs.g"]
                == iter_i.get_data_idx()["outputs.g"]
            )


@pytest.mark.integration
def test_subset_sim_DAMASK_Mg_two_level_parameter_flow(new_null_config, tmp_path):

    # use `new_null_config` because currently these workflows include template components
    wk = mf.make_demo_workflow("subset_simulation_DAMASK_Mg_two_level", path=tmp_path)

    num_elements = wk.tasks.initialise_markov_chains.num_elements

    for elem_idx in range(num_elements):

        # input of `generate_next_state` from either `initialise_markov_chains`,
        # `increment_chain_inner`, or `increment_chain`:

        init_iters = {
            i.loop_idx["levels"]: i
            for i in wk.tasks.initialise_markov_chains.elements[elem_idx].iterations
        }
        gen_next_iters = {
            (
                i.loop_idx["inner_markov_chain"],
                i.loop_idx["outer_markov_chain"],
                i.loop_idx["levels"],
            ): i
            for i in wk.tasks.generate_next_state.elements[elem_idx].iterations
        }
        inc_chain_inner_iters = {
            (
                i.loop_idx["inner_markov_chain"],
                i.loop_idx["outer_markov_chain"],
                i.loop_idx["levels"],
            ): i
            for i in wk.tasks.increment_chain_inner.elements[elem_idx].iterations
        }
        inc_chain_iters = {
            (i.loop_idx["outer_markov_chain"], i.loop_idx["levels"]): i
            for i in wk.tasks.increment_chain.elements[elem_idx].iterations
        }

        for l_idx, iter_i in gen_next_iters.items():
            if (
                l_idx[0] == 0 and l_idx[1] == 0
            ):  # inner and outer MC loop zeroth iterations
                assert (
                    iter_i.get_data_idx()["inputs.x"]
                    == init_iters[l_idx[2]].get_data_idx()["outputs.x"]
                )

            elif l_idx[0] == 0:  # inner MC loop zeroth iteration, outer MC loop non-zero
                # should be sourced from `increment_chain`
                for lj_idx, iter_j in inc_chain_iters.items():
                    if lj_idx[1] == l_idx[2] and lj_idx[0] == l_idx[1] - 1:
                        assert (
                            iter_i.get_data_idx()["inputs.x"]
                            == iter_j.get_data_idx()["outputs.x"]
                        )

            elif l_idx[0] > 0:  # inner MC loop non-zero iteration:
                # should be sourced from `increment_chain_inner`, previous inner iteration, same outer MC loop iteration
                for lj_idx, iter_j in inc_chain_inner_iters.items():
                    if (
                        lj_idx[2] == l_idx[2]
                        and lj_idx[0] == l_idx[0] - 1
                        and lj_idx[1] == l_idx[1]
                    ):
                        assert (
                            iter_i.get_data_idx()["inputs.x"]
                            == iter_j.get_data_idx()["outputs.x"]
                        )
            else:
                raise RuntimeError(f"no test for loop index: {l_idx}")

        # new state from generate_next_state inner MC used in inner MC system_analysis and increment_chain_inner
        # keys are: (inner_markov_chain, outer_markov_chain, levels)
        gen_next_iters = {
            (
                i.loop_idx["inner_markov_chain"],
                i.loop_idx["outer_markov_chain"],
                i.loop_idx["levels"],
            ): i
            for i in wk.tasks.generate_next_state.elements[elem_idx].iterations
        }
        pre_proc_iters = {
            (
                i.loop_idx["inner_markov_chain"],
                i.loop_idx["outer_markov_chain"],
                i.loop_idx["levels"],
            ): i
            for i in wk.tasks.generate_volume_element_from_voronoi_random_variates_2.elements[
                elem_idx
            ].iterations
        }
        model_iters = {
            (
                i.loop_idx["inner_markov_chain"],
                i.loop_idx["outer_markov_chain"],
                i.loop_idx["levels"],
            ): i
            for i in wk.tasks.simulate_VE_loading_damask_2.elements[elem_idx].iterations
        }
        limit_iters = {
            (
                i.loop_idx["inner_markov_chain"],
                i.loop_idx["outer_markov_chain"],
                i.loop_idx["levels"],
            ): i
            for i in wk.tasks.evaluate_yield_stress_limit_state_2.elements[
                elem_idx
            ].iterations
        }

        # check parameter flow within inner MC chain:

        for l_idx, iter_i in gen_next_iters.items():
            assert (
                pre_proc_iters[l_idx].get_data_idx()["inputs.x"]
                == iter_i.get_data_idx()["outputs.x"]
            )
            assert (
                inc_chain_inner_iters[l_idx].get_data_idx()["inputs.x"]
                == iter_i.get_data_idx()["outputs.x"]
            )

        for l_idx, iter_i in pre_proc_iters.items():
            assert (
                model_iters[l_idx].get_data_idx()["inputs.volume_element"]
                == iter_i.get_data_idx()["outputs.volume_element"]
            )

        for l_idx, iter_i in model_iters.items():
            assert (
                limit_iters[l_idx].get_data_idx()["inputs.yield_stress"]
                == iter_i.get_data_idx()["outputs.yield_stress"]
            )

        for l_idx, iter_i in limit_iters.items():
            assert (
                inc_chain_inner_iters[l_idx].get_data_idx()["inputs.g"]
                == iter_i.get_data_idx()["outputs.g"]
            )

        # check parameter flow into outer MC chain from inner MC chain:
        # keys are: (outer_markov_chain, levels)

        pre_proc_iters = {
            (i.loop_idx["outer_markov_chain"], i.loop_idx["levels"]): i
            for i in wk.tasks.generate_volume_element_from_voronoi_random_variates_3.elements[
                elem_idx
            ].iterations
        }
        model_iters = {
            (i.loop_idx["outer_markov_chain"], i.loop_idx["levels"]): i
            for i in wk.tasks.simulate_VE_loading_damask_3.elements[elem_idx].iterations
        }
        limit_iters = {
            (i.loop_idx["outer_markov_chain"], i.loop_idx["levels"]): i
            for i in wk.tasks.evaluate_yield_stress_limit_state_3.elements[
                elem_idx
            ].iterations
        }

        # final inner MC chain iterations only:
        inc_chain_inner_max_iters = {}
        max_inner_iter = wk.loops.inner_markov_chain.num_iterations - 1
        for i in wk.tasks.increment_chain_inner.elements[elem_idx].iterations:
            if i.loop_idx["inner_markov_chain"] == max_inner_iter:
                inc_chain_inner_max_iters[
                    (i.loop_idx["outer_markov_chain"], i.loop_idx["levels"])
                ] = i

        for l_idx, iter_i in inc_chain_inner_max_iters.items():
            assert (
                pre_proc_iters[l_idx].get_data_idx()["inputs.x"]
                == iter_i.get_data_idx()["outputs.x"]
            )
            assert (
                inc_chain_iters[l_idx].get_data_idx()["inputs.x"]
                == iter_i.get_data_idx()["outputs.x"]
            )

        for l_idx, iter_i in pre_proc_iters.items():
            assert (
                model_iters[l_idx].get_data_idx()["inputs.volume_element"]
                == iter_i.get_data_idx()["outputs.volume_element"]
            )

        for l_idx, iter_i in model_iters.items():
            assert (
                limit_iters[l_idx].get_data_idx()["inputs.yield_stress"]
                == iter_i.get_data_idx()["outputs.yield_stress"]
            )

        for l_idx, iter_i in limit_iters.items():
            assert (
                inc_chain_iters[l_idx].get_data_idx()["inputs.g"]
                == iter_i.get_data_idx()["outputs.g"]
            )
