import numpy as np
import scipy.stats as stats
import scipy.optimize as optimize

def negative_log_likelihood_t(degrees_of_freedom, standardized_data):
    """
    Objective function to minimize: the negative log-likelihood of a 
    Student t-distribution for a given degrees of freedom.
    """
    # Ensure degrees of freedom is strictly positive to avoid errors
    if degrees_of_freedom <= 0:
        return np.inf
        
    # Calculate the log probability density for each observation
    log_pdfs = stats.t.logpdf(standardized_data, df=degrees_of_freedom)
    
    # Return the negative sum of log likelihoods
    return -np.sum(log_pdfs)

def fit_student_t_mle(returns_data):
    """
    Standardizes the data and fits the degrees of freedom parameter 
    using Maximum Likelihood Estimation.
    """
    # 1. Standardize the data (mean 0, variance 1)
    sample_mean = np.mean(returns_data)
    sample_std = np.std(returns_data, ddof=1) # using sample std
    standardized_data = (returns_data - sample_mean) / sample_std
    
    # 2. Set an initial guess for the degrees of freedom
    initial_guess = [5.0]
    
    # 3. Minimize the negative log-likelihood
    # We use bounds to ensure the degrees of freedom remains > 0
    result = optimize.minimize(
        fun=negative_log_likelihood_t,
        x0=initial_guess,
        args=(standardized_data,),
        bounds=[(1.1, 100.0)] # DF usually between slightly >1 and 100 in finance
    )
    
    if result.success:
        estimated_df = result.x[0]
        return estimated_df
    else:
        raise ValueError("Optimization failed to converge.")

# Note: To replicate Example I.3.17 exactly, you would pass the specific 
# daily log returns of the FTSE 100 from Jan 2004 to Aug 2007 into fit_student_t_mle().