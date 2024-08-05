from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from typing import List
from dotenv import load_dotenv
from discovery import WatsonDiscoveryCE
import os
import json
import time
import io
# from ibm_watson import DiscoveryV2
# from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from requests.exceptions import ConnectionError, ReadTimeout

# Load environment variables
# load_dotenv()
# API_KEY = os.getenv("API_KEY")
# IBM_CLOUD_URL = os.getenv("IBM_CLOUD_URL")
# PROJECT_ID = os.getenv("PROJECT_ID")
# COLLECTION_ID = os.getenv("COLLECTION_ID")
# VERSION = '2020-08-30'

load_dotenv()

cloud_url = os.getenv("cloud_url", None)
d_p_id = os.getenv("d_project_id", None)
d_key = os.getenv("d_api_key", None)
discovery_coll_id =os.getenv("collection_id", None)
discovery_url = os.getenv("discovery_url", None)
VERSION = '2020-08-30'

# Initialize FastAPI app
app = FastAPI()

# Initialize IBM Watson Discovery
print(cloud_url)
discovery = WatsonDiscoveryCE(param_api_key=d_key,
                                    param_url=discovery_url,
                                    proj_id=d_p_id,
                                    param_ibm_cloud_url=cloud_url,
                                    discovery_coll_id= discovery_coll_id
                                )


# Query Document from discovery
# def check_document_content(project_id, collection_id, document_id):
#     try:
#         response = discovery.query(
#           project_id=project_id,
#           filter="document_id::" + document_id,
#         natural_language_query=''
#         ).get_result()
#         print("res:", response['results'])
#         if not response['results']:
#             return "OCR result is not ready yet"
#         else:
#             return response['results'][0]['text']
    

#     except Exception as e:
#          print(f"An error occurred: {str(e)}")


#print("full doc text:", text)

   
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Read file content
        file_content = await file.read()
        
        # Upload file to IBM Watson Discovery
        print(f"Uploading file: {file.filename}")
        response = discovery.add_document(
            project_id=d_p_id,
            collection_id=discovery_coll_id,
            file=file_content,
            filename=file.filename,
            file_content_type=file.content_type,
            #**timeout_settings
        ).get_result()
        
        # Return the document ID for later querying
        document_id = response['document_id']
        print(f"Uploaded document ID: {document_id}")
        return JSONResponse(content={"document_id": document_id})
    except (ConnectionError, ReadTimeout) as e:
        error_message = f"Connection error or timeout processing file {file.filename}: {str(e)}"
        print(error_message)
        return JSONResponse(content={"error": error_message, "filename": file.filename})
    except Exception as e:
        error_message = f"Error processing file {file.filename}: {str(e)}"
        print(error_message)
        return JSONResponse(content={"error": error_message, "filename": file.filename})

@app.get("/query/{document_id}")
async def query_status(document_id: str):
    try:
        # Fetch the extracted text using a query with retries
        query_response = discovery.query_full_text(document_id, discovery.discovery_coll_id)
        print(f"Query Result for document ID {document_id}:")
        print(query_response)
        return JSONResponse(content=query_response)
    except (ConnectionError, ReadTimeout) as e:
        error_message = f"Connection error or timeout querying document ID {document_id}: {str(e)}"
        print(error_message)
        return JSONResponse(content={"error": error_message, "document_id": document_id})
    except Exception as e:
        error_message = f"Error querying document ID {document_id}: {str(e)}"
        print(error_message)
        return JSONResponse(content={"error": error_message, "document_id": document_id})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
