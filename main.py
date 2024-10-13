import os
import csv
import time
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials

# Set up Computer Vision Client
subscription_key = os.getenv("VISION_KEY")
endpoint = os.getenv("VISION_ENDPOINT")
computervision_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))

# Set folder path for images and ground truth
image_folder_path = "./images"
groundtruth_folder_path = "./groundtruth"
output_file_path = './output.csv'

# Loop over each file in the image folder
for filename in os.listdir(image_folder_path):
    image_path = os.path.join(image_folder_path, filename)

    # Only process image files
    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
        with open(image_path, "rb") as image_data:
            # Call API for each image
            read_response = computervision_client.read_in_stream(image_data, raw=True)
            read_operation_location = read_response.headers.get("Operation-Location")

            if not read_operation_location:
                print(f"Could not obtain Operation-Location for {filename}. Skipping...")
                continue

            operation_id = read_operation_location.split("/")[-1]

            # Wait for the operation to complete
            while True:
                read_result = computervision_client.get_read_result(operation_id)
                if read_result.status not in ['notStarted', 'running']:
                    break
                time.sleep(1)

            # Get the expected result from the corresponding text file in the groundtruth folder
            expected_file_path = os.path.join(groundtruth_folder_path, filename.replace('.jpg', '.txt').replace('.png', '.txt').replace('.jpeg', '.txt').replace('.bmp', '.txt'))
            expected_text = ''
            if os.path.exists(expected_file_path):
                with open(expected_file_path, 'r') as expected_file:
                    expected_text = expected_file.read().strip()
            else:
                expected_text = 'Not Found'

            # Prepare the predicted result
            predicted_text = ''
            if read_result.status == "succeeded":
                for page in read_result.analyze_result.read_results:
                    for line in page.lines:
                        predicted_text += line.text + ' '

            # Trim spaces from the predicted text
            predicted_text = predicted_text.strip()  # Remove leading and trailing spaces

            # Get the expected result from the corresponding text file in the groundtruth folder
            expected_file_path = os.path.join(groundtruth_folder_path, filename.replace('.jpg', '.txt').replace('.png', '.txt').replace('.jpeg', '.txt').replace('.bmp', '.txt'))
            expected_text = ''
            if os.path.exists(expected_file_path):
                with open(expected_file_path, 'r') as expected_file:
                    expected_text = expected_file.read().strip()  # Remove leading and trailing spaces
            else:
                expected_text = 'Not Found'

            # Determine if the predicted output is correct
            is_correct = 'correct' if expected_text.replace(" ", "").lower() == predicted_text.replace(" ", "").lower() else 'wrong'

            # Write the result to the CSV
            with open(output_file_path, mode='a', newline='', encoding='utf-8') as output_file:
                csv_writer = csv.writer(output_file)
                csv_writer.writerow([filename, expected_text, predicted_text, is_correct])
