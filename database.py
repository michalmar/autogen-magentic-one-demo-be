import os
from azure.cosmos import CosmosClient, PartitionKey
from azure.identity import DefaultAzureCredential

# Get Cosmos DB account details from environment variables
COSMOS_URI = os.getenv("COSMOS_URI", "https://YOURDB.documents.azure.com:443/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "ag_demo")
CONTAINER_NAME = os.getenv("CONTAINER_NAME", "ag_demo")

def get_db():
    """
    Returns the Cosmos DB container.
    """
    # # Use DefaultAzureCredential for AAD token authorization
    # credential = DefaultAzureCredential()

    # # Initialize the Cosmos client with AAD token authorization
    # client = CosmosClient(COSMOS_URI, credential=credential)

    # # Create the database if it does not exist
    # database = client.create_database_if_not_exists(id=DATABASE_NAME)

    # # Create the container if it does not exist.
    # # Adjust the partition key and throughput as needed.
    # container = database.create_container_if_not_exists(
    #     id=CONTAINER_NAME,
    #     partition_key=PartitionKey(path="/user_id"),
    #     offer_throughput=400
    # ) 
    # return container
    return True
