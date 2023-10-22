import azure.functions as func
import logging
import jwt
import json
import requests
from azure.storage.blob import BlobServiceClient

def store_to_container(connection_string, container_name, csv_data, file_name):
    # Create aBlobServiceClient using the connection string
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    # Get a reference to the container
    container_client = blob_service_client.get_container_client(container_name)
    # Upload the CSV data to a blob in the container
    blob_client = container_client.get_blob_client(file_name)
    blob_client.upload_blob(csv_data, overwrite=True)
    print("DataFrame successfully written to Azure Storage container.")

def retreive_from_container(connection_string, container_name, file_name):
    # Create aBlobServiceClient using the connection string
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    # Get a reference to the container
    container_client = blob_service_client.get_container_client(container_name)
    # Download the blob to a local file
    blob_client = container_client.get_blob_client(file_name)
    with open(file_name, "wb") as my_blob:
        blob_data = blob_client.download_blob()
        blob_data.readinto(my_blob)
    print("Blob data successfully downloaded.")

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="Resource_API")
def Resource_API(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    #print the header of the request
    
    logging.info(req.headers.get('state'))
    logging.info( req.params.get('state'))
    name =  req.params.get('state')
    code =  req.params.get('code')
    # decode name using jwt and a secret key
    decoded_name = None
    if name:
        try:
            decoded_name = jwt.decode(name, 'SFGBER345345#$%#$fefe', algorithms=['HS256'])
            userid = decoded_name.get('userid')
            # create json file with userid
    
            # Make Strava auth API call with your 
            # client_code, client_secret and code
            response = requests.post(
                                url = 'https://www.strava.com/oauth/token',
                                data = {
                                        'client_id': 13077,
                                        'client_secret': 'eff7509ab872e832466790aa0da2be7d1a40a568',
                                        'code': code,
                                        'grant_type': 'authorization_code'
                                        }
                            ,verify=False)
            #Save json response as a variable
            strava_tokens = response.json()
            # Save tokens to a stringvariable
            #strava_tokens = json.dumps(strava_tokens)
                       


            json_data = json.dumps({ "userid2": strava_tokens })
            # store json file in blob storage
            store_to_container('DefaultEndpointsProtocol=https;AccountName=testbi2q;AccountKey=3stbiTyAoo4bRRRbPR0vBitfLz7OE06JbVrmMVd3mFXP6no8oVvMjkg4lhPWMxLvOJIC7EWD+VtT+ASt3E/oEg==;EndpointSuffix=core.windows.net', 'stravakeys', json_data, 'userid.json')
            # retreive json file from blob storage
            filecontents = retreive_from_container('DefaultEndpointsProtocol=https;AccountName=testbi2q;AccountKey=3stbiTyAoo4bRRRbPR0vBitfLz7OE06JbVrmMVd3mFXP6no8oVvMjkg4lhPWMxLvOJIC7EWD+VtT+ASt3E/oEg==;EndpointSuffix=core.windows.net', 'stravakeys', 'userid.json')
            logging.info(filecontents)
            logging.info(decoded_name)
        except jwt.ExpiredSignatureError:
            return func.HttpResponse(
                "The authorization token has expired.",
                status_code=401
            )
        except jwt.InvalidTokenError:
            return func.HttpResponse(
                "The authorization token is invalid.",
                status_code=401
            )        

    if decoded_name:
        return func.HttpResponse(userid)
    else:
        return func.HttpResponse(
             "No valid authorization header was provided in the request.",
             status_code=401
        )
