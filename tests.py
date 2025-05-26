import time

def sum_of_squares_formula(n):
    return (n * (n + 1) * (2 * n + 1)) // 6

N = 10**6  # One million

# Measure execution time
start_time = time.time()
result = sum_of_squares_formula(N)
end_time = time.time()

execution_time = end_time - start_time
print(f"Result: {result}")
print(f"Execution Time: {execution_time:.10f} seconds")
