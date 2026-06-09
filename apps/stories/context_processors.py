def global_context(request):
    """
    Inyecta datos globales en las plantillas:
    - Categorías de historias
    - Páginas legales activas
    - Perfiles de redes sociales configurados
    - Banners publicitarios activos por su posición
    """
    from apps.stories.models import Category, Banner
    from apps.legal.models import LegalPage
    from apps.social_links.models import SocialNetwork

    # Manejo de excepciones para evitar fallos cuando no se han ejecutado las migraciones aún
    try:
        categories = Category.objects.all()
        banner_arriba = Banner.objects.filter(position='arriba', is_active=True).first()
        banner_abajo = Banner.objects.filter(position='abajo', is_active=True).first()
        banner_lateral = Banner.objects.filter(position='lateral', is_active=True).first()
        banner_entre_historias = Banner.objects.filter(position='entre_historias', is_active=True).first()
    except Exception:
        categories = []
        banner_arriba = banner_abajo = banner_lateral = banner_entre_historias = None

    try:
        legal_pages = LegalPage.objects.filter(is_active=True)
    except Exception:
        legal_pages = []

    try:
        social_networks = SocialNetwork.objects.filter(is_active=True)
    except Exception:
        social_networks = []

    return {
        'all_categories': categories,
        'banner_arriba': banner_arriba,
        'banner_abajo': banner_abajo,
        'banner_lateral': banner_lateral,
        'banner_entre_historias': banner_entre_historias,
        'legal_pages': legal_pages,
        'social_networks': social_networks,
    }
