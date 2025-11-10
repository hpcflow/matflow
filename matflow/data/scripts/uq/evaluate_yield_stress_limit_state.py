def evaluate_yield_stress_limit_state(threshold_yield_stress, yield_stress):
    return {"g": threshold_yield_stress - yield_stress}
