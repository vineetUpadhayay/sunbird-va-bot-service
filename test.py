import requests
import time

# Define the URL
url = "http://127.0.0.1:8000/api/core/query/"

# Define the first request body
payload1 = {
    "query": "Why does President Biden emphasize the importance of passing the Bipartisan Infrastructure Law?"
}

# Make the first POST request
start_time1 = time.time()
response1 = requests.post(url, json=payload1)
end_time1 = time.time()

# Print the response for the first request
print("Response 1:")
print(response1.json())
print("Time taken for Request 1:", end_time1 - start_time1, "seconds")
#Time taken for Request 1: 2.2567005157470703 seconds


# Define the second request body
payload2 = {
    "query": "What is the significance of President Biden stressing the need to pass the Bipartisan Infrastructure Law?"
}

# Make the second POST request
start_time2 = time.time()
response2 = requests.post(url, json=payload2)
end_time2 = time.time()

# Print the response for the second request
print("\nResponse 2:")
print(response2.json())
print("Time taken for Request 2:", end_time2 - start_time2, "seconds")
#Time taken for Request 2: 0.0970001220703125 seconds


# Calculate the time difference between the two requests
time_difference = end_time2 - start_time1
print("\nTime difference between requests:", time_difference, "seconds")
#requests: 2.3547005653381348 seconds

