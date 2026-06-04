import numpy as np

def analyze_quantiles(data_array, percentiles_to_calculate):
    """
    Calculates specific percentiles for a given data sample.
    Addresses the interpolation issue mentioned in the text by using numpy's linear interpolation.
    """
    data = np.array(data_array)
    
    print(f"Data Array: {data}")
    print(f"Sorted Data: {np.sort(data)}\n")
    
    print("--- Percentile Analysis ---")
    for p in percentiles_to_calculate:
        # np.percentile uses linear interpolation by default, which is standard in quantitative finance
        value = np.percentile(data, p, method='linear')
        print(f"{p}th Percentile: {value:.4f}")

# --- Testing with Examples from the text ---
if __name__ == "__main__":
    # The text uses the example of {1, 2, 3, ..., 10} and {1, 2, 3, ..., 11}
    # to demonstrate quirks in Excel's 10th percentile calculation.
    
    data_1 = np.arange(1, 11) # Array: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    data_2 = np.arange(1, 12) # Array: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    
    # We want to check the 10th percentile (p=10), Median (p=50), and 90th percentile (p=90)
    percentiles = [10, 50, 90]
    
    print("Dataset 1: 1 to 10")
    analyze_quantiles(data_1, percentiles)
    
    print("\nDataset 2: 1 to 11")
    analyze_quantiles(data_2, percentiles)