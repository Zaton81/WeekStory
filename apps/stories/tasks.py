"""
Tareas de Celery para historias
"""
from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task
def publish_scheduled_stories():
    """
    Publica automáticamente historias programadas cuya fecha ya ha pasado.
    Se ejecuta periódicamente vía Celery Beat.
    """
    from apps.stories.models import Story

    now = timezone.now()
    scheduled_stories = Story.objects.filter(
        status='scheduled',
        scheduled_at__lte=now
    )

    count = 0
    for story in scheduled_stories:
        story.status = 'published'
        story.published_at = now
        story.save(update_fields=['status', 'published_at', 'updated_at'])
        logger.info(f"Historia '{story.title}' (ID: {story.id}) publicada automáticamente.")
        count += 1

    if count:
        logger.info(f"Total: {count} historia(s) programada(s) publicada(s).")
    return count


def _clean_html_to_text(html_content):
    """
    Limpia el contenido HTML de una historia para obtener texto plano legible
    con una estructura natural para la síntesis de voz.
    """
    import re
    from django.utils.html import strip_tags

    text = html_content

    # Convertir saltos de línea HTML en marcadores de párrafo
    text = re.sub(r'</p>\s*<p[^>]*>', '\n\n', text)
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'</?(h[1-6]|div|blockquote|li|ul|ol)[^>]*>', '\n', text)

    # Eliminar todas las etiquetas HTML restantes
    text = strip_tags(text)

    # Decodificar entidades HTML comunes
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&quot;', '"')
    text = text.replace('&apos;', "'")
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&ndash;', '–')
    text = text.replace('&mdash;', '—')
    text = text.replace('&hellip;', '...')
    text = text.replace('&laquo;', '«')
    text = text.replace('&raquo;', '»')

    # Limpiar espacios múltiples en cada línea
    text = re.sub(r'[ \t]+', ' ', text)

    # Normalizar saltos de línea múltiples a máximo 2 (separador de párrafo)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def _split_text_for_tts(text):
    """
    Divide el texto en fragmentos (chunks) procesables por el modelo TTS,
    respetando los límites de oraciones y párrafos para pausas naturales.
    Devuelve una lista de tuplas: (texto_fragmento, es_fin_de_parrafo).
    """
    import re

    # Dividir en párrafos primero
    paragraphs = text.split('\n\n')
    chunks = []

    for para_idx, paragraph in enumerate(paragraphs):
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        # Dividir cada párrafo en oraciones
        sentences = re.split(r'(?<=[.!?…»"])\s+', paragraph)
        sentences = [s.strip() for s in sentences if s.strip()]

        for sent_idx, sentence in enumerate(sentences):
            is_last_sentence = (sent_idx == len(sentences) - 1)
            chunks.append((sentence, is_last_sentence))

    return chunks


@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def generate_story_audio_task(self, story_id):
    """
    Sintetiza la lectura de la historia en un archivo de audio WAV usando Kokoro TTS local.
    Selecciona aleatoriamente entre las voces españolas ef_dora (femenina) y em_alex (masculina).
    Divide el texto por oraciones (chunking) para evitar límites de contexto del modelo.
    """
    from apps.stories.models import Story
    import io
    import random
    import numpy as np
    from django.core.files.base import ContentFile
    import soundfile as sf
    from kokoro_onnx import Kokoro

    logger.info(f"Iniciando síntesis de audio para la historia {story_id}...")

    try:
        story = Story.objects.get(id=story_id)

        # Actualizar estado a procesando
        story.audio_status = 'processing'
        story.audio_error = ''
        story.save(update_fields=['audio_status', 'audio_error'])

        # Limpiar texto de HTML con procesamiento mejorado
        text = _clean_html_to_text(story.content)

        if not text:
            raise ValueError("El contenido de la historia está vacío.")

        # Seleccionar voz aleatoria entre las voces españolas disponibles
        SPANISH_VOICES = ['ef_dora', 'em_alex']
        selected_voice = random.choice(SPANISH_VOICES)
        logger.info(f"Voz seleccionada para historia {story_id}: {selected_voice}")

        # Dividir texto en fragmentos procesables
        chunks = _split_text_for_tts(text)

        if not chunks:
            raise ValueError("No se encontraron oraciones para sintetizar.")

        # Cargar modelo local (usar v1.0 si está disponible, con fallback a v0.19)
        import os
        model_v1_path = '/app/models/tts/kokoro-v1.0.onnx'
        model_v019_path = '/app/models/tts/kokoro-v0_19.onnx'
        voices_path = '/app/models/tts/voices-v1.0.bin'

        model_path = model_v1_path if os.path.exists(model_v1_path) else model_v019_path
        logger.info(f"Usando modelo TTS: {os.path.basename(model_path)}")

        kokoro = Kokoro(model_path, voices_path)

        audio_chunks = []
        sample_rate = 24000  # Default sample rate for Kokoro

        # Silencio entre oraciones y párrafos
        SENTENCE_PAUSE_SECS = 0.30
        PARAGRAPH_PAUSE_SECS = 0.65

        for i, (sentence, is_paragraph_end) in enumerate(chunks):
            logger.info(f"Sintetizando fragmento {i+1}/{len(chunks)} de historia {story_id}...")

            try:
                samples, sr = kokoro.create(
                    sentence,
                    voice=selected_voice,
                    speed=0.95,
                    lang='es'
                )
                sample_rate = sr
                audio_chunks.append(samples)
            except Exception as chunk_err:
                logger.warning(f"Error en fragmento {i+1}: {chunk_err}. Continuando...")
                continue

            # Añadir pausa entre fragmentos
            pause_secs = PARAGRAPH_PAUSE_SECS if is_paragraph_end else SENTENCE_PAUSE_SECS
            silence = np.zeros(int(sample_rate * pause_secs), dtype=np.float32)
            audio_chunks.append(silence)

        if not audio_chunks:
            raise ValueError("No se pudo sintetizar ningún fragmento de audio.")

        # Concatenar todos los fragmentos
        final_samples = np.concatenate(audio_chunks)

        # Guardar en memoria como WAV
        buffer = io.BytesIO()
        sf.write(buffer, final_samples, sample_rate, format='WAV')
        buffer.seek(0)

        # Guardar archivo en el modelo
        file_name = f"story_{story.id}.wav"
        if story.audio_file:
            try:
                story.audio_file.delete(save=False)
            except Exception as e:
                logger.warning(f"No se pudo eliminar el archivo de audio anterior: {e}")

        story.audio_file.save(file_name, ContentFile(buffer.read()), save=False)
        story.audio_status = 'completed'
        story.audio_error = ''
        story.audio_voice = selected_voice
        story.save(update_fields=['audio_file', 'audio_status', 'audio_error', 'audio_voice', 'updated_at'])

        logger.info(f"Síntesis de audio para historia {story_id} completada exitosamente con voz {selected_voice}.")
        return {'status': 'completed', 'story_id': story_id, 'voice': selected_voice}

    except Story.DoesNotExist:
        logger.error(f"Historia {story_id} no encontrada.")
        raise
    except Exception as exc:
        logger.error(f"Error generando audio para historia {story_id}: {str(exc)}")
        try:
            story = Story.objects.get(id=story_id)
            story.audio_status = 'failed'
            story.audio_error = str(exc)
            story.save(update_fields=['audio_status', 'audio_error'])
        except Exception:
            pass
        # Reintentar la tarea de fondo en caso de error
        raise self.retry(exc=exc, countdown=120)
