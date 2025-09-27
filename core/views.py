from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from django.conf import settings


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_language(request):
    """
    API endpoint to set the user's language preference.
    Accepts a POST request with 'language' field, e.g. {"language": "ta"}
    """
    language = request.data.get('language')

    if not language:
        return Response(
            {'error': _('Language code is required.')},
            status=status.HTTP_400_BAD_REQUEST
        )

    if language not in [lang[0] for lang in settings.LANGUAGES]:
        return Response(
            {'error': _('Unsupported language code.')},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Set the language for the current session
    translation.activate(language)
    request.session[settings.LANGUAGE_SESSION_KEY] = language

    # Optionally save language preference to user profile
    # if hasattr(request.user, 'language_preference'):
    #     request.user.language_preference = language
    #     request.user.save(update_fields=['language_preference'])

    return Response({
        'message': _('Language changed successfully.'),
        'language': language,
        'language_name': dict(settings.LANGUAGES).get(language, language)
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_languages(request):
    """
    API endpoint to get list of available languages.
    """
    languages = [
        {
            'code': lang[0],
            'name': lang[1],
            'current': lang[0] == translation.get_language()
        }
        for lang in settings.LANGUAGES
    ]

    return Response({
        'languages': languages,
        'current_language': translation.get_language()
    }, status=status.HTTP_200_OK)
