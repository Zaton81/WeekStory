"""
AI Service - Comunicación con Ollama para extracción de texto y generación de posts sociales.
"""
import json
import re
import time
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# Modelo Ollama por defecto
DEFAULT_MODEL = 'llama3.2:3b'


class OllamaService:
    """Servicio para interactuar con Ollama (LLM local)."""

    def __init__(self):
        self.base_url = getattr(settings, 'OLLAMA_API_URL', 'http://ollama:11434')
        self.model = DEFAULT_MODEL
        self.timeout = 240  # segundos

    def is_available(self) -> bool:
        """Verifica si Ollama está accesible."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

    def _generate(self, prompt: str, temperature: float = 0.7, json_format: bool = False) -> str:
        """Envía un prompt a Ollama y devuelve la respuesta completa."""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": 2048,
                }
            }
            if json_format:
                payload["format"] = "json"

            resp = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "").strip()
        except requests.exceptions.Timeout:
            logger.error("Ollama timeout: el modelo tardó demasiado en responder.")
            raise
        except requests.exceptions.ConnectionError:
            logger.error(f"No se pudo conectar con Ollama en {self.base_url}")
            raise
        except Exception as e:
            logger.error(f"Error al comunicarse con Ollama: {e}")
            raise

    def _parse_json_response(self, text: str) -> dict:
        """Intenta extraer un objeto JSON de la respuesta de Ollama."""
        # Buscar JSON en bloques de código
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Buscar JSON directo en la respuesta
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        return {}

    def summarize_story(self, title: str, content: str, category: str = "") -> dict:
        """
        Resume una historia y extrae entidades usando Ollama.
        
        Returns:
            dict con claves: extracted_text, entities, confidence_score, model_version, processing_time_ms
        """
        start_time = time.time()

        # Limpiar HTML del contenido
        clean_content = re.sub(r'<[^>]+>', '', content)
        # Truncar a un máximo razonable para el modelo
        max_chars = 6000
        if len(clean_content) > max_chars:
            clean_content = clean_content[:max_chars] + "..."

        prompt = f"""Eres un asistente experto en análisis literario. Analiza la siguiente historia y devuelve ÚNICAMENTE un JSON válido (sin texto adicional) con esta estructura exacta:

{{
  "resumen": "Un resumen conciso de 2-4 oraciones del argumento principal de la historia.",
  "personajes": ["lista", "de", "nombres", "de", "personajes"],
  "ubicaciones": ["lista", "de", "lugares", "mencionados"],
  "temas": ["tema1", "tema2"]
}}

Título: {title}
{f"Categoría: {category}" if category else ""}

Texto de la historia:
{clean_content}

Responde SOLO con el JSON, sin explicaciones ni texto adicional."""

        try:
            response_text = self._generate(prompt, temperature=0.3, json_format=True)
            parsed = self._parse_json_response(response_text)

            processing_time = int((time.time() - start_time) * 1000)

            if parsed and "resumen" in parsed:
                return {
                    'extracted_text': parsed.get('resumen', ''),
                    'entities': {
                        'characters': parsed.get('personajes', []),
                        'locations': parsed.get('ubicaciones', []),
                        'themes': parsed.get('temas', []),
                    },
                    'confidence_score': 0.85 if len(parsed.get('resumen', '')) > 50 else 0.6,
                    'model_version': self.model,
                    'processing_time_ms': processing_time,
                }
            else:
                # Respuesta no parseada: usar el texto directamente como resumen
                logger.warning("No se pudo parsear JSON de Ollama, usando respuesta como texto plano.")
                return {
                    'extracted_text': response_text[:500] if response_text else clean_content[:300],
                    'entities': {'characters': [], 'locations': [], 'themes': []},
                    'confidence_score': 0.4,
                    'model_version': self.model,
                    'processing_time_ms': processing_time,
                }

        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            logger.error(f"Error en summarize_story: {e}")
            # Fallback: usar extracto del texto
            return {
                'extracted_text': clean_content[:300] + "..." if len(clean_content) > 300 else clean_content,
                'entities': {'characters': [], 'locations': [], 'themes': []},
                'confidence_score': 0.2,
                'model_version': f'{self.model} (fallback)',
                'processing_time_ms': processing_time,
            }

    def generate_social_posts(self, title: str, summary: str, category: str = "") -> dict:
        """
        Genera posts optimizados para cada red social.

        Returns:
            dict con claves: twitter, linkedin, instagram, facebook.
            Cada una contiene: {text: str, hashtags: str}
        """
        prompt = f"""Eres un experto en marketing digital y redes sociales. Genera publicaciones atractivas para compartir una historia/artículo en redes sociales.

Título del artículo: {title}
Resumen: {summary}
{f"Categoría: {category}" if category else ""}

Genera ÚNICAMENTE un JSON válido con esta estructura (sin texto adicional):

{{
  "twitter": {{
    "text": "Texto del tweet (máximo 250 caracteres, deja espacio para hashtags). Usa tono directo y atractivo.",
    "hashtags": "#hashtag1 #hashtag2 #hashtag3"
  }},
  "linkedin": {{
    "text": "Texto profesional y narrativo para LinkedIn (2-3 párrafos cortos). Tono reflexivo y profesional.",
    "hashtags": "#hashtag1 #hashtag2 #hashtag3 #hashtag4"
  }},
  "instagram": {{
    "text": "Caption emotivo con emojis para Instagram. Cuenta una breve historia que invite a leer más.",
    "hashtags": "#hashtag1 #hashtag2 #hashtag3 #hashtag4 #hashtag5 #hashtag6 #hashtag7 #hashtag8 #hashtag9 #hashtag10 #escritura #literatura #historias #leer #lectura"
  }},
  "facebook": {{
    "text": "Texto casual y enganchador para Facebook. Haz una pregunta o invita a la reflexión.",
    "hashtags": "#hashtag1 #hashtag2 #hashtag3"
  }}
}}

IMPORTANTE:
- Los hashtags de Instagram deben ser 15-20 hashtags relevantes al contenido.
- Los hashtags de Twitter deben ser 3-5 como máximo.
- Todos los textos deben ser en español.
- No incluyas enlaces en el texto, se añadirán automáticamente.
- Responde SOLO con el JSON."""

        try:
            response_text = self._generate(prompt, temperature=0.8, json_format=True)
            parsed = self._parse_json_response(response_text)

            if parsed and 'twitter' in parsed:
                result = {}
                for platform in ['twitter', 'linkedin', 'instagram', 'facebook']:
                    platform_data = parsed.get(platform, {})
                    result[platform] = {
                        'text': platform_data.get('text', f'📖 {title}'),
                        'hashtags': platform_data.get('hashtags', f'#historias #lectura #{category.lower()}' if category else '#historias #lectura'),
                    }
                return result
            else:
                logger.warning("No se pudo parsear JSON de posts sociales, generando fallback.")
                return self._fallback_social_posts(title, summary, category)

        except Exception as e:
            logger.error(f"Error al generar posts sociales: {e}")
            return self._fallback_social_posts(title, summary, category)

    def _fallback_social_posts(self, title: str, summary: str, category: str = "") -> dict:
        """Genera posts sociales básicos sin IA."""
        short_summary = summary[:150] + "..." if len(summary) > 150 else summary
        cat_tag = f"#{category.lower().replace(' ', '')}" if category else "#historias"
        base_hashtags = f"#lectura #escritura #literatura {cat_tag}"

        return {
            'twitter': {
                'text': f"📖 {title}\n\n{short_summary[:200]}",
                'hashtags': f"#lectura #escritura {cat_tag}",
            },
            'linkedin': {
                'text': f"📚 Nueva publicación: {title}\n\n{short_summary}\n\n¿Qué os parece esta historia?",
                'hashtags': f"#lectura #escritura #literatura {cat_tag}",
            },
            'instagram': {
                'text': f"📖✨ {title}\n\n{short_summary}\n\n¿Ya la leíste? Cuéntanos qué te pareció 👇",
                'hashtags': f"{base_hashtags} #libros #leer #bookstagram #escritor #relatos #cuentos #narrativa #ficcion #leeresvivir #amoleer #mundoliterario #letras #palabras",
            },
            'facebook': {
                'text': f"📖 {title}\n\n{short_summary}\n\n¿Qué opinas? ¡Déjanos tu comentario! 💬",
                'hashtags': f"#lectura #escritura {cat_tag}",
            },
        }
