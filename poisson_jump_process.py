import numpy as np
import scipy.stats as stats

def calculate_poisson_probability(lam, dt, x_jumps):
    """
    Calculates the exact probability of observing 'x_jumps' in an interval 'dt'
    given an arrival rate 'lam' (lambda).
    """
    # Expected number of events in interval dt
    expected_events = lam * dt 
    
    # Calculate probability using the Poisson PMF
    prob = stats.poisson.pmf(x_jumps, mu=expected_events)
    return prob

def simulate_jump_indicator(lam, dt, steps):
    """
    Simulates a jump indicator process q(t). 
    Returns an array of 1s (jump occurred) and 0s (no jump) for each time step.
    Probability of a jump in interval dt is approximately lam * dt.
    """
    jump_probabilities = np.random.uniform(0, 1, steps)
    jump_threshold = lam * dt
    
    # Indicator is 1 if the random number is less than the jump probability
    indicators = np.where(jump_probabilities < jump_threshold, 1, 0)
    return indicators