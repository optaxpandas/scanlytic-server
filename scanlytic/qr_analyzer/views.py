from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from server.models import QR
from server.serializers import UploadTableSerializer, QRSerializer
from django.conf import settings
from scanlytic.utils import JWT, Utils
import virustotal_python
from base64 import urlsafe_b64encode
import cv2
import os
from datetime import datetime
from django.utils.timezone import make_aware

# Create your views here.
class QRAnalyzer(APIView):
    def get(self, request):
        utils = Utils()
        try:
            JWT.verifyToken(request)
            serializer = UploadTableSerializer(data=request.FILES)
            if(serializer.is_valid()):
                fileName = request.FILES['file']
                print(serializer.data)
                # fileName = serializer.data.get('file')
                image_path = os.path.join(settings.MEDIA_ROOT, fileName.name)
                with open(image_path, "wb+") as destination:
                    for chunk in fileName.chunks():
                        destination.write(chunk)
                
                # read the QRCODE image
                image = cv2.imread(image_path)
                detector = cv2.QRCodeDetector()
                url, vertices_array, binary_qrcode = detector.detectAndDecode(image)
                print('URL: ', url)

                with virustotal_python.Virustotal(settings.VIRUS_TOTAL) as vtotal:
                    resp = vtotal.request("urls", data={"url": url}, method="POST")
                    # Safe encode URL in base64 format
                    url_id = urlsafe_b64encode(url.encode()).decode().strip("=")
                    report = vtotal.request(f"urls/{url_id}")
                    # Extract relevant data
                    data = report.data.get("attributes", {})
                    analysis_stats = data.get("last_analysis_stats", {})
                    last_analysis_results = data.get("last_analysis_results", {})
                    
                    # Format results
                    first_submission_date = make_aware(datetime.strptime(datetime.utcfromtimestamp(data.get("first_submission_date")).strftime("%Y-%m-%d %H:%M:%S UTC"), '%Y-%m-%d %H:%M:%S UTC'))
                    last_analysis_date = make_aware(datetime.strptime(datetime.utcfromtimestamp(data.get("last_analysis_date")).strftime("%Y-%m-%d %H:%M:%S UTC"), '%Y-%m-%d %H:%M:%S UTC'))
                    
                    analysis_summary = {
                        "url": url,
                        "times_submitted": data.get("times_submitted"),
                        "first_submission_date": first_submission_date,
                        "last_analysis_date": last_analysis_date,
                        "reputation": data.get("reputation"),
                        "total_votes": data.get("total_votes"),
                        "last_analysis_stats": analysis_stats,
                    }

                    # Extract a few key security vendor results
                    selected_results = {vendor: result["result"] for vendor, result in last_analysis_results.items() if vendor in ["Google Safebrowsing", "BitDefender", "Kaspersky", "Sophos"]}

                    malicious_count = analysis_stats.get("malicious", 0)

                    if malicious_count <= 2:
                        security_score = 10 - (malicious_count * 1)
                        risk_level = "Safe"
                    elif malicious_count <= 7:
                        security_score = 10 - (malicious_count * 1.5)
                        risk_level = "Risky"
                    else:
                        security_score = max(0, 10 - (malicious_count * 2))
                        risk_level = "Critical"


                    security_score = round(security_score, 1)
                    # Full report structure
                    report_data = {
                        "summary": analysis_summary,
                        "detection_results": selected_results,
                        "category": data.get("categories"),
                        "tags": data.get("tags"),
                        "security_score": security_score,
                        "risk_level": risk_level,
                    }

                    data = QR.objects.create(
                        user_id = str(request.user['user_id']),
                        image = image_path,
                        url = url,
                        first_submission_date = first_submission_date,
                        last_analysis_date = last_analysis_date,
                        reputation = data.get("reputation"),
                        total_malicious_votes = data.get("total_votes").get('malicious'),
                        total_harmless_votes = data.get("total_votes").get('harmless'),
                        malicious = malicious_count,
                        suspicious = analysis_stats.get('suspicious'),
                        harmless = analysis_stats.get('harmless'),
                        security_score = security_score,
                        risk_level = risk_level
                    )

                    data = QRSerializer(data).data

                    print('report data: ',report_data)

                    return Response(utils.createResponse(message=settings.MESSAGES['REPORT_GENERATED'], data=data), status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except virustotal_python.VirustotalError as error:
            print('ERROR: ', error)
            return Response(utils.createResponse(settings.MESSAGES['REQUEST_COULD_NOT_BE_COMPLETED'], str(error)), status=status.HTTP_400_BAD_REQUEST)

        except Exception as error:
            print('ERROR: ',error)
            status_code = status.HTTP_403_FORBIDDEN if isinstance(error, AuthenticationFailed) else status.HTTP_500_INTERNAL_SERVER_ERROR
            message = settings.MESSAGES['FORBIDDEN'] if isinstance(error, AuthenticationFailed) else settings.MESSAGES['INTERNAL_SERVER_ERROR']

            response = utils.createResponse(message, str(error))
            return Response(response, status=status_code)
