# TDEI-python-lib-osw-inclination
Calculates the Incline of given edges 

## Introduction 
Service to adds the inclination to the existing edges.geojson file, the service does the following:
- Listens to the topic which is mentioned in `.env` file for any new message, example  `REQUEST_TOPIC=test_request` 
- Consumes the message and perform following checks - 
  - Download the zip file locally 
  - unzip it and read the edges.geojson file
  - Calculate the edge geometry boundary box
  - Download the DEM file from NED 1/3 arc-second
  - Process the DEM file and calculate the inclination
  - Add the inclination to the edges.geojson file 
- Publishes the result to the topic mentioned in `.env` file, example `RESPONSE_TOPIC=test_response`

## Getting Started
The project is built on Python with FastAPI framework. All the regular nuances for a Python project are valid for this.

### System requirements
| Software   | Version |
|------------|---------|
| Python     | 3.10.x  |


### Connectivity to cloud
- Connecting this to cloud will need the following in the `.env` file

```bash
QUEUECONNECTION=xxx
STORAGECONNECTION=xxx
REQUEST_TOPIC=xxx
REQUEST_SUBSCRIPTION=xxx
RESPONSE_TOPIC=xxx
CONTAINER_NAME=xxx
MAX_CONCURRENT_MESSAGES=xx
```

The application connect with the `STORAGECONNECTION` string provided in `.env` file and validates downloaded zipfile using `python-osw-validation` package.
`QUEUECONNECTION` is used to send out the messages and listen to messages.

`MAX_CONCURRENT_MESSAGES` is the maximum number of concurrent messages that the service can handle. If not provided, defaults to 1

## Establishing python env for the project
Running the code base requires a proper Python environment set up. The following lines of code helps one establish such env named `tdei-osw`. replace `tdei-osw` with the name of your choice.

```
conda create -n tdei-osw python==3.10.3 gdal
conda activate tdei-osw
pip install -r requirements.txt
```
Alternatively one can use the `setup_env.sh` script provided with this repo. One can run 
`source ./setup_env.sh`. Once run, the command creates an environment with the name `tdei`

### How to Set up and Build
Follow the steps to install the python packages required for both building and running the application

1. Setup virtual environment
    ```
    python3.10 -m venv .venv
    source .venv/bin/activate
    ```

2. Install the dependencies. Run the following command in terminal on the same directory as `requirements.txt`
    ```
    # Installing requirements
    pip install -r requirements.txt
    ```
### How to Run the Server/APIs   

1. The http server by default starts with `8000` port
2. Run server
    ```
    uvicorn src.main:app --reload
    ```
3. By default `get` call on `localhost:8000/health` gives a sample response
4. Other routes include a `ping` with get and post. Make `get` or `post` request to `http://localhost:8000/health/ping`
5. Once the server starts, it will start to listening the subscriber(`REQUEST_SUBSCRIPTION` should be in env file)

#### Request Format
```json
  {
    "messageId": "tdei_record_id",
    "messageType": "workflow_identifier",
    "data": {
      "file_url": "file_upload_path"
    } 
  }
```

#### Response Format
```json
  {
    "messageId": "tdei_record_id",
    "messageType": "workflow_identifier",
    "data": {
      "file_url": "file_upload_path",
      "updated_file_url": "file_upload_path", // updated file url whicjh contains the inclination added
      "success": true/false,
      "status": "Success/Failed"
    },
  "publishedDate": "published date"
  }
```


### How to Set up and run the Tests

Make sure you have set up the project properly before running the tests, see above for `How to Setup and Build`.


#### How to run unit test cases
1. `.env` file is not required for Unit test cases.
2To run the coverage
   1. `python -m coverage run --source=src -m unittest discover -s tests/unit_tests`
   2. Above command will run all the unit test cases.
   3. To generate the coverage report in console
      1. `coverage report`
      2. Above command will generate the code coverage report in terminal. 
   4. To generate the coverage report in html.
      1. `coverage html`
      2. Above command will generate the html report, and generated html would be in `htmlcov` directory at the root level.
   5. _NOTE :_ To run the `html` or `report` coverage, 3.i) command is mandatory

