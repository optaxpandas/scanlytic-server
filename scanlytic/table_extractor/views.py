from datetime import datetime
import os
import csv
import openpyxl
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from scanlytic.utils import JWT, Utils
from server.models import Table, User
from server.serializers import TableSerializer, UploadTableSerializer
from rest_framework.exceptions import AuthenticationFailed
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient

class TableExtractor(APIView):
    # Get all the tables for the particular user
    def get(self, request):
        utils = Utils()
        try:
            JWT.verifyToken(request)
            tables = Table.objects.filter(user_id=request.user['user_id'])

            serealized_data = TableSerializer(tables, many=True).data
            for table in serealized_data:
                image_path = table.get("image")
                content_path = table.get("content")

                # Convert to Base64
                table["image_base64"] = utils.encodeFileToBase64(image_path) if image_path else None
                table["file_base64"] = utils.encodeFileToBase64(content_path) if content_path else None

                # Include file names
                table["image_name"] = os.path.basename(image_path) if image_path else None
                table["file_name"] = os.path.basename(content_path) if content_path else None
                
            
            response = utils.createResponse(message='Table Found', data=serealized_data)
            return Response(response, status=status.HTTP_200_OK)

        except Exception as error:
            print('Error: ',error)
            status_code = status.HTTP_403_FORBIDDEN if isinstance(error, AuthenticationFailed) else status.HTTP_500_INTERNAL_SERVER_ERROR
            message = settings.MESSAGES['FORBIDDEN'] if isinstance(error, AuthenticationFailed) else settings.MESSAGES['INTERNAL_SERVER_ERROR']

            response = utils.createResponse(message, str(error))
            return Response(response, status=status_code)
        
    # Extract a table out of an Image returns the URL of the final file
    def post(self, request):
        utils = Utils()
        try:
            JWT.verifyToken(request)
            serializer = UploadTableSerializer(data=request.data)
            if(serializer.is_valid()):
                # image_path = serializer.validated_data['image_path']
                # file_name = serializer.validated_data['name']

                image_url = serializer.validated_data['image_url']
                file_name = serializer.validated_data['file_name']
                format = serializer.validated_data['format']

                print(image_url)
                print(file_name)
                print('type: ',format)

                
                # Initialize Azure Document Intelligence client
                endpoint = settings.AZURE_DOCUMENT_INTELLIGENCE["ENDPOINT"]
                api_key = settings.AZURE_DOCUMENT_INTELLIGENCE["API_KEY"]
                model_id = settings.AZURE_DOCUMENT_INTELLIGENCE["MODEL_ID"]

                client = DocumentIntelligenceClient(endpoint, AzureKeyCredential(api_key))

                # with open(image_path, "rb") as file_data:
                poller = client.begin_analyze_document(model_id, AnalyzeDocumentRequest(url_source=image_url))
                result = poller.result()

                # Extract tables and structure the data
                extracted_tables = []
                for table in result.tables:
                    structured_table = []
                    for row_index in range(table.row_count):
                        row_data = [""] * table.column_count
                        for cell in table.cells:
                            if cell.row_index == row_index:
                                row_data[cell.column_index] = cell.content
                        structured_table.append(row_data)
                    extracted_tables.append(structured_table)

                # Generate Excel File
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f'{timestamp}_{file_name}.{format}'
                excel_path = os.path.join(settings.MEDIA_ROOT, filename)
                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = "Extracted Table"

                if(format == "xlsx"):
                    # Create an excel file
                    wb = openpyxl.Workbook()
                    ws = wb.active
                    ws.title = "Extracted Table"

                    for table in extracted_tables:
                        for row in table:
                            ws.append(row)
                        ws.append([])  # Empty row for separation

                    wb.save(excel_path)

                elif(format == "csv"):
                    # Create a csv file
                    with open(excel_path, mode="w", newline="", encoding="utf-8") as file:
                        writer = csv.writer(file)
                        for table in extracted_tables:
                            writer.writerows(table)
                            writer.writerow([])  # Empty row for separation


                # Upload Excel file to Azure Blob Storage
                blob_service_client = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
                container_client = blob_service_client.get_container_client(settings.AZURE_CONTAINER_NAME)
                blob_client = container_client.get_blob_client(filename)
                
                with open(excel_path, "rb") as data:
                    blob_client.upload_blob(data, overwrite=True)


                # Construct the file URL
                excel_url = f"https://{settings.AZURE_ACCOUNT_NAME}.blob.core.windows.net/{settings.AZURE_CONTAINER_NAME}/{filename}"

                if os.path.exists(excel_path):
                    os.remove(excel_path)
                    print(f"Deleted local file: {excel_path}")
                

                table = Table.objects.create(
                    user_id = request.user['user_id'],
                    image = image_url,
                    file_type = 'xlsx',
                    content = excel_url
                )
                
                # Return File URL
                return Response(utils.createResponse(message=settings.MESSAGES['TABLE_EXTRACTED'], data={ 'file': excel_url, 'file_name': filename }), status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            print('Error: ',error)
            status_code = status.HTTP_403_FORBIDDEN if isinstance(error, AuthenticationFailed) else status.HTTP_500_INTERNAL_SERVER_ERROR
            message = settings.MESSAGES['FORBIDDEN'] if isinstance(error, AuthenticationFailed) else settings.MESSAGES['INTERNAL_SERVER_ERROR']

            response = utils.createResponse(message, str(error))
            return Response(response, status=status_code)
        

class FetchTable(APIView):
    # Fetch a particular table by its ID
    def get(self, request, table_id):
        utils = Utils()
        try:
            JWT.verifyToken(request)
            table = Table.objects.get(table_id=table_id)
            image_path = table.image
            content_path = table.content
            # Convert to Base64
            image_base64 = utils.encodeFileToBase64(image_path) if image_path else None
            file_base64 = utils.encodeFileToBase64(content_path) if content_path else None
            # Include file names
            image_name = os.path.basename(image_path) if image_path else None
            file_name = os.path.basename(content_path) if content_path else None
            
            data = {
                'table_id': str(table.table_id),
                'image': image_name,
                'image_base64': image_base64,
                'file_type': table.file_type,
                'file_name': file_name,
                'file_base64': file_base64,
                'content_type': table.content,
                'created_on': table.created_on,
                'updated_on': table.updated_on,
            }

            response = utils.createResponse(message='Table Found', data=data)
            return Response(response, status=status.HTTP_200_OK)

        except Exception as error:
            print('Error: ',error)
            status_code = status.HTTP_403_FORBIDDEN if isinstance(error, AuthenticationFailed) else status.HTTP_500_INTERNAL_SERVER_ERROR
            message = settings.MESSAGES['FORBIDDEN'] if isinstance(error, AuthenticationFailed) else settings.MESSAGES['INTERNAL_SERVER_ERROR']

            response = utils.createResponse(message, str(error))
            return Response(response, status=status_code)