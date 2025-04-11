def evaluate_yield_stress_limit_state(x, threshold_yield_stress, yield_stress):
    return {"g": threshold_yield_stress - yield_stress}
