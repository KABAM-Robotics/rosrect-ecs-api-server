import json
import requests

# Test case - ERROR
errorText = "Aborting because the robot appears to be oscillating over and over. Even after executing all recovery behaviors"

# Test case - WARN Turtlebot
# errorText = "Rotation cmd in collision"

# Test case - Info Turtlebot
# errorText = "Got new plan"

# Test case - NO RESULT
# errorText = "Sample dummy error text."

# Test case - tests pattern matching
# errorText = "Clearing both costmaps to unstuck robot (3.00m)."
# errorText = "Clearing both costmaps to unstuck robot (1.84m)."

# Test case - tests case insensitivity
# errorText = "got new plan"
# errorText = "GOT NEW PLAN"

print(errorText)
robotModel = "Turtlebot3"
query_params = {'RobotModel': robotModel, 'ErrorText': errorText}
error_response = requests.get('http://localhost:8000' + '/api/ert/getErrorData/', params = query_params)
print(error_response)
error_resp_content = json.loads(error_response.content)
error_data = error_resp_content['data']

print('ERT RESPONSE')
if (len(error_data) > 0):
    error_info = error_data[0]
    ecc = error_info['error_level']
    print(ecc)
else:
    print('Normal operation resumes.')

print('ECS RESPONSE')
error_response = requests.get('http://localhost:8000' + '/api/ecs/getErrorData/', params = query_params)
print(error_response)
error_resp_content = json.loads(error_response.content)
error_data = error_resp_content['data']

if (len(error_data) > 0):
    error_info = error_data[0]
    ecc = error_info['severity']
    print(ecc)
else:
    print('Normal operation resumes.')