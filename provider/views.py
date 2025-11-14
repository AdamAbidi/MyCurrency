from provider.models import Provider
from provider.serializers import ProviderSerializer
from provider.validators import validate_priority

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

class ProviderViewSet(viewsets.ModelViewSet):
    queryset = Provider.objects.all()
    serializer_class = ProviderSerializer

    @action(detail=True, methods=['post'], url_path='toggle')
    def toggle_active(self, request: Request, pk=None)-> Response:
        # Get the provider instance using the primary key from the URL
        provider = self.get_object()

        # Toggle the is_active flag
        provider.is_active = not provider.is_active

        # Save the updated provider state
        provider.save()

        # Return the new active status in the response
        return Response({
            'is_active': provider.is_active
        }, status=status.HTTP_200_OK)



    @action(detail=True, methods=['post'], url_path='set-priority')
    def set_priority(self, request: Request, pk=None)-> Response:
        # Validate and get the new priority value
        try:
            new_priority = validate_priority(request.data["priority"])
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Get the provider instance based on URL pk
        provider = self.get_object()

        # If the priority hasn't changed, do nothing
        if provider.priority == new_priority:
            return Response({"status": "priority update not needed"})

        # Apply the new priority and save the provider
        provider.priority = new_priority
        provider.save()

        # Return a success response
        return Response({"status": "priority updated", "new_priority": new_priority})
