"""
Social Media Publishers - Lógica de publicación para cada plataforma.

Cada publisher soporta un modo simulado: si las credenciales son placeholder
(contienen 'your-'), el publisher logueará el intento y retornará éxito simulado.
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def _is_placeholder(value: str) -> bool:
    """Comprueba si un valor de credencial es un placeholder."""
    if not value:
        return True
    return value.startswith('your-') or value == ''


def get_publisher(platform: str):
    """Factoría que devuelve el publisher adecuado para una plataforma."""
    publishers = {
        'twitter': TwitterPublisher,
        'facebook': FacebookPublisher,
        'linkedin': LinkedInPublisher,
        'instagram': InstagramPublisher,
    }
    cls = publishers.get(platform)
    if not cls:
        raise ValueError(f"Plataforma no soportada: {platform}")
    return cls()


class BasePublisher:
    """Clase base para publishers de redes sociales."""
    
    platform_name = "Base"
    
    def publish(self, text: str, image_url: str = None) -> dict:
        raise NotImplementedError
    
    def _simulate(self, text: str) -> dict:
        """Simula una publicación cuando las credenciales no están configuradas."""
        logger.info(
            f"[SIMULADO] Publicación en {self.platform_name}: "
            f"{text[:100]}..."
        )
        return {
            'success': True,
            'post_id': f'sim_{self.platform_name.lower()}_{id(text)}',
            'post_url': '',
            'error': '',
            'simulated': True,
        }


class TwitterPublisher(BasePublisher):
    """Publisher para Twitter/X usando Tweepy."""
    
    platform_name = "Twitter/X"
    
    def publish(self, text: str, image_url: str = None) -> dict:
        api_key = getattr(settings, 'TWITTER_API_KEY', '')
        api_secret = getattr(settings, 'TWITTER_API_SECRET', '')
        access_token = getattr(settings, 'TWITTER_ACCESS_TOKEN', '')
        access_token_secret = getattr(settings, 'TWITTER_ACCESS_TOKEN_SECRET', '')
        
        if any(_is_placeholder(v) for v in [api_key, api_secret, access_token, access_token_secret]):
            return self._simulate(text)
        
        try:
            import tweepy
            client = tweepy.Client(
                consumer_key=api_key,
                consumer_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_token_secret,
            )
            
            # Truncar a 280 caracteres para Twitter
            tweet_text = text[:280]
            
            response = client.create_tweet(text=tweet_text)
            tweet_id = response.data['id']
            
            return {
                'success': True,
                'post_id': str(tweet_id),
                'post_url': f'https://twitter.com/i/web/status/{tweet_id}',
                'error': '',
            }
        except Exception as e:
            logger.error(f"Error publicando en Twitter: {e}")
            return {
                'success': False,
                'post_id': '',
                'post_url': '',
                'error': str(e),
            }


class FacebookPublisher(BasePublisher):
    """Publisher para Facebook usando facebook-sdk."""
    
    platform_name = "Facebook"
    
    def publish(self, text: str, image_url: str = None) -> dict:
        access_token = getattr(settings, 'FACEBOOK_ACCESS_TOKEN', '')
        
        if _is_placeholder(access_token):
            return self._simulate(text)
        
        try:
            import facebook
            graph = facebook.GraphAPI(access_token=access_token)
            
            response = graph.put_object(
                parent_object='me',
                connection_name='feed',
                message=text,
            )
            post_id = response.get('id', '')
            
            return {
                'success': True,
                'post_id': post_id,
                'post_url': f'https://www.facebook.com/{post_id}' if post_id else '',
                'error': '',
            }
        except Exception as e:
            logger.error(f"Error publicando en Facebook: {e}")
            return {
                'success': False,
                'post_id': '',
                'post_url': '',
                'error': str(e),
            }


class LinkedInPublisher(BasePublisher):
    """Publisher para LinkedIn usando la API REST."""
    
    platform_name = "LinkedIn"
    
    def publish(self, text: str, image_url: str = None) -> dict:
        client_id = getattr(settings, 'LINKEDIN_CLIENT_ID', '')
        client_secret = getattr(settings, 'LINKEDIN_CLIENT_SECRET', '')
        
        if any(_is_placeholder(v) for v in [client_id, client_secret]):
            return self._simulate(text)
        
        try:
            import requests as req
            
            # LinkedIn requiere un access_token OAuth2 vigente.
            # Esta implementación es un placeholder para cuando el flujo OAuth
            # esté completamente implementado.
            logger.warning("LinkedIn OAuth2 flow not fully implemented. Simulating publish.")
            return self._simulate(text)
            
        except Exception as e:
            logger.error(f"Error publicando en LinkedIn: {e}")
            return {
                'success': False,
                'post_id': '',
                'post_url': '',
                'error': str(e),
            }


class InstagramPublisher(BasePublisher):
    """Publisher para Instagram usando la Graph API de Meta."""
    
    platform_name = "Instagram"
    
    def publish(self, text: str, image_url: str = None) -> dict:
        username = getattr(settings, 'INSTAGRAM_USERNAME', '')
        password = getattr(settings, 'INSTAGRAM_PASSWORD', '')
        
        if any(_is_placeholder(v) for v in [username, password]):
            return self._simulate(text)
        
        try:
            # Instagram requiere una imagen para publicar.
            # Si no hay imagen, simulamos la publicación.
            if not image_url:
                logger.warning("Instagram requiere una imagen para publicar. Simulando publicación.")
                return self._simulate(text)
            
            # La API de Instagram a través de la Graph API de Meta requiere
            # una cuenta de negocio y permisos aprobados. 
            # Simulamos hasta que el flujo OAuth esté completamente implementado.
            logger.warning("Instagram Graph API flow not fully implemented. Simulating publish.")
            return self._simulate(text)
            
        except Exception as e:
            logger.error(f"Error publicando en Instagram: {e}")
            return {
                'success': False,
                'post_id': '',
                'post_url': '',
                'error': str(e),
            }
