def global_context(request):
    """
    Inyecta datos globales en las plantillas:
    - Categorías de historias
    - Páginas legales activas
    - Perfiles de redes sociales configurados
    - Banners publicitarios activos por su posición
    - Páginas personales activas (navbar)
    """
    from apps.stories.models import Category, Banner
    from apps.legal.models import LegalPage
    from apps.social_links.models import SocialNetwork
    from apps.pages.models import Page

    # Manejo de excepciones para evitar fallos cuando no se han ejecutado las migraciones aún
    try:
        categories = list(Category.objects.all())
        active_banners = list(Banner.objects.filter(is_active=True))
        banner_arriba = next((b for b in active_banners if b.position == 'arriba'), None)
        banner_abajo = next((b for b in active_banners if b.position == 'abajo'), None)
        banner_lateral = next((b for b in active_banners if b.position == 'lateral'), None)
        banner_entre_historias = next((b for b in active_banners if b.position == 'entre_historias'), None)
    except Exception:
        categories = []
        banner_arriba = banner_abajo = banner_lateral = banner_entre_historias = None

    try:
        legal_pages = list(LegalPage.objects.filter(is_active=True))
    except Exception:
        legal_pages = []

    try:
        social_networks = list(SocialNetwork.objects.filter(is_active=True))
    except Exception:
        social_networks = []

    try:
        personal_pages = list(Page.objects.filter(is_active=True, show_in_navbar=True))
    except Exception:
        personal_pages = []

    return {
        'all_categories': categories,
        'banner_arriba': banner_arriba,
        'banner_abajo': banner_abajo,
        'banner_lateral': banner_lateral,
        'banner_entre_historias': banner_entre_historias,
        'legal_pages': legal_pages,
        'social_networks': social_networks,
        'personal_pages': personal_pages,
    }
