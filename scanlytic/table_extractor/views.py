from datetime import datetime
import os
import base64
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

class TableExtractor(APIView):
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
        
    def post(self, request):
        utils = Utils()
        try:
            JWT.verifyToken(request)
            serializer = UploadTableSerializer(data=request.FILES)
            if(serializer.is_valid()):
                print("IN TABLE EXTRACTOR: ", serializer.validated_data['file'])
                
                uploaded_file = request.FILES["file"]

                image_path = os.path.join(settings.MEDIA_ROOT, uploaded_file.name)
                with open(image_path, "wb+") as destination:
                    for chunk in uploaded_file.chunks():
                        destination.write(chunk)

                # Initialize Azure Document Intelligence client
                endpoint = settings.AZURE_DOCUMENT_INTELLIGENCE["ENDPOINT"]
                api_key = settings.AZURE_DOCUMENT_INTELLIGENCE["API_KEY"]
                model_id = settings.AZURE_DOCUMENT_INTELLIGENCE["MODEL_ID"]

                client = DocumentIntelligenceClient(endpoint, AzureKeyCredential(api_key))

                with open(image_path, "rb") as file_data:
                    poller = client.begin_analyze_document(model_id, file_data)
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
                excel_filename = f'{timestamp}_{os.path.splitext(uploaded_file.name)[0]}.xlsx'
                excel_path = os.path.join(settings.MEDIA_ROOT, excel_filename)
                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = "Extracted Table"

                # Write table data into Excel
                for table in extracted_tables:
                    for row in table:
                        ws.append(row)  # Append row to Excel file
                    ws.append([])  # Empty row between tables

                wb.save(excel_path)

                # Convert Excel file to Base64
                with open(excel_path, "rb") as excel_file:
                    encoded_string = base64.b64encode(excel_file.read()).decode("utf-8")
                
                print('=======================================')
                print('base 64: \n',encoded_string)
                print('=======================================')

                table = Table.objects.create(
                    user_id = request.user['user_id'],
                    image = image_path,
                    file_type = 'xlsx',
                    content = excel_path
                )
                
                # Return Base64 response
                return Response(utils.createResponse(message=settings.MESSAGES['TABLE_EXTRACTED'], data={ 'file': encoded_string, 'file_name': excel_filename }), status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            print('Error: ',error)
            status_code = status.HTTP_403_FORBIDDEN if isinstance(error, AuthenticationFailed) else status.HTTP_500_INTERNAL_SERVER_ERROR
            message = settings.MESSAGES['FORBIDDEN'] if isinstance(error, AuthenticationFailed) else settings.MESSAGES['INTERNAL_SERVER_ERROR']

            response = utils.createResponse(message, str(error))
            return Response(response, status=status_code)
        

class FetchTable(APIView):
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