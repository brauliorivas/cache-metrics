import powerlaw
from collections import Counter


def fit_powerlaw_from_reader(reader, discrete=True, verbose=False):
    """
    Fit a power law to a cache access trace using the jeffalstott/powerlaw library.

    Parameters
    ----------
    reader   : libCacheSim-style reader (objects with .obj_id)
    discrete : bool - True for cache traces (counts are integers)
    verbose  : bool - print fit summary

    Returns
    -------
    results  : powerlaw.Fit object
        results.power_law.alpha   → the exponent s
        results.power_law.xmin    → where the power law starts
    """
    freq = Counter(req.obj_id for req in reader)
    counts = list(freq.values())

    results = powerlaw.Fit(counts, discrete=discrete, verbose=verbose)

    if verbose:
        print(f"Exponent (alpha/s) : {results.power_law.alpha:.4f}")
        print(f"x_min              : {results.power_law.xmin}")
        R, p = results.distribution_compare("power_law", "lognormal")
        print(f"Power law vs lognormal: R={R:.3f}, p={p:.3f}")
        print("  (R > 0 favors power law, R < 0 favors lognormal)")

    return results
