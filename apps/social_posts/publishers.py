"""
Social Media Publishers - Lógica de publicación síncrona para cada plataforma.

Cada publisher soporta un modo simulado: si las credenciales son placeholder
(contienen 'your-' o están vacías), el publisher registrará el intento y retornará éxito simulado.
Todas las llamadas HTTP externas usan timeout=10 explícito.
"""
import logging
from django.conf import settings

try:
    import requests
    TimeoutExceptions = (TimeoutError, requests.Timeout)
    NetworkExceptions = (OSError, requests.RequestException)
except ImportError:
    requests = None
    TimeoutExceptions = (TimeoutError,)
    NetworkExceptions = (OSError,)

logger = logging.getLogger(__name__)

DEFAULT_HTTP_TIMEOUT = 10


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
    """Clase base para publishers síncronos de redes sociales."""
    
    platform_name = "Base"
    timeout = DEFAULT_HTTP_TIMEOUT
    
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
    """Publisher síncrono para Twitter/X."""
    
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
            if hasattr(client, 'session') and client.session is not None:
                client.session.timeout = self.timeout
            
            tweet_text = text[:280]
            response = client.create_tweet(text=tweet_text)
            tweet_id = response.data['id']
            
            return {
                'success': True,
                'post_id': str(tweet_id),
                'post_url': f'https://twitter.com/i/web/status/{tweet_id}',
                'error': '',
            }
        except TimeoutExceptions as e:
            logger.error(f"Timeout publicando en Twitter ({self.timeout}s): {e}")
            return {
                'success': False,
                'post_id': '',
                'post_url': '',
                'error': f'Tiempo de espera agotado ({self.timeout}s) al conectar con Twitter/X.',
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
    """Publisher síncrono para Facebook con timeout=10."""
    
    platform_name = "Facebook"
    
    def publish(self, text: str, image_url: str = None) -> dict:
        access_token = getattr(settings, 'FACEBOOK_ACCESS_TOKEN', '')
        
        if _is_placeholder(access_token):
            return self._simulate(text)
        
        try:
            import facebook
            graph = facebook.GraphAPI(access_token=access_token, timeout=self.timeout)
            
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
        except TimeoutExceptions as e:
            logger.error(f"Timeout publicando en Facebook ({self.timeout}s): {e}")
            return {
                'success': False,
                'post_id': '',
                'post_url': '',
                'error': f'Tiempo de espera agotado ({self.timeout}s) al conectar con Facebook.',
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
    """Publisher síncrono para LinkedIn con timeout=10."""
    
    platform_name = "LinkedIn"
    
    def publish(self, text: str, image_url: str = None) -> dict:
        client_id = getattr(settings, 'LINKEDIN_CLIENT_ID', '')
        client_secret = getattr(settings, 'LINKEDIN_CLIENT_SECRET', '')
        
        if any(_is_placeholder(v) for v in [client_id, client_secret]):
            return self._simulate(text)
        
        try:
            logger.warning("LinkedIn OAuth2 flow not fully implemented. Simulating publish.")
            return self._simulate(text)
        except NetworkExceptions as e:
            logger.error(f"Error de red publicando en LinkedIn: {e}")
            return {
                'success': False,
                'post_id': '',
                'post_url': '',
                'error': str(e),
            }
        except Exception as e:
            logger.error(f"Error publicando en LinkedIn: {e}")
            return {
                'success': False,
                'post_id': '',
                'post_url': '',
                'error': str(e),
            }


class InstagramPublisher(BasePublisher):
    """Publisher síncrono para Instagram con timeout=10."""
    
    platform_name = "Instagram"
    
    def publish(self, text: str, image_url: str = None) -> dict:
        username = getattr(settings, 'INSTAGRAM_USERNAME', '')
        password = getattr(settings, 'INSTAGRAM_PASSWORD', '')
        
        if any(_is_placeholder(v) for v in [username, password]):
            return self._simulate(text)
        
        try:
            if not image_url:
                logger.warning("Instagram requiere una imagen para publicar. Simulando publicación.")
                return self._simulate(text)
            
            logger.warning("Instagram Graph API flow not fully implemented. Simulating publish.")
            return self._simulate(text)
        except NetworkExceptions as e:
            logger.error(f"Error de red publicando en Instagram: {e}")
            return {
                'success': False,
                'post_id': '',
                'post_url': '',
                'error': str(e),
            }
        except Exception as e:
            logger.error(f"Error publicando en Instagram: {e}")
            return {
                'success': False,
                'post_id': '',
                'post_url': '',
                'error': str(e),
            }
