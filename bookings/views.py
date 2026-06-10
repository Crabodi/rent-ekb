from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_view(request):
    """Тестовый эндпоинт для проверки работы bookings"""
    return Response({
        'message': 'Bookings app is working!',
        'user': request.user.username
    })