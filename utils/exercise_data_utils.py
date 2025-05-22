def estimate_1rm(reps, weight, formula="epley"):
    if reps <= 0 or weight <= 0:
        return None

    formula = formula.lower()

    if formula == "epley":
        return weight * (1 + reps / 30)
    elif formula == "brzycki":
        return weight * (36 / (37 - reps))
    elif formula == "lombardi":
        return weight * (reps ** 0.10)
    elif formula == "mayhew":
        return (100 * weight) / (52.2 + 41.9 * (2.71828 ** (-0.055 * reps)))
    elif formula == "oconner":
        return weight * (1 + 0.025 * reps)
    else:
        # Default fallback to Epley if unknown
        return weight * (1 + reps / 30)

