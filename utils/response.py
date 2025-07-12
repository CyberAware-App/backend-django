from rest_framework.response import Response

class ResponseMixin:
    @staticmethod
    def success_response(data=None, message="Success", status="success", status_code=200):
        return Response({
            "status": status,
            "message": message,
            "data": data
        }, status=status_code)

    @staticmethod
    def error_response(errors=None, message="Bad Request", status="error", status_code=400):
        return Response({
            "status": status,
            "message": message,
            "errors": errors
        }, status=status_code)
    
    