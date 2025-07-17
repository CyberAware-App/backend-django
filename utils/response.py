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
    
    @staticmethod
    def format_serializer_errors(serializer_errors):
        """
        Format serializer errors to handle both field-specific and non-field errors
        """
        formatted_errors = {}
        for field, errors in serializer_errors.items():
            if field == 'non_field_errors':
                # Handle non-field errors by adding them to a general field
                formatted_errors['general'] = errors[0] if isinstance(errors, list) else errors
            else:
                # Handle field-specific errors
                formatted_errors[field] = errors[0] if isinstance(errors, list) else errors
        return formatted_errors
    
    