from azure.storage.blob import BlobServiceClient

connection_string = 'DefaultEndpointsProtocol=https;AccountName=testbi2q;AccountKey=3stbiTyAoo4bRRRbPR0vBitfLz7OE06JbVrmMVd3mFXP6no8oVvMjkg4lhPWMxLvOJIC7EWD+VtT+ASt3E/oEg==;EndpointSuffix=core.windows.net'
container_name = 'stravakeys' 


def store_to_container(csv_data, file_name):
    # Create aBlobServiceClient using the connection string
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    # Get a reference to the container
    container_client = blob_service_client.get_container_client(container_name)
    # Upload the CSV data to a blob in the container
    blob_client = container_client.get_blob_client(file_name)
    blob_client.upload_blob(csv_data, overwrite=True)
    print("DataFrame successfully written to Azure Storage container.")

def retreive_from_container(file_name):
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