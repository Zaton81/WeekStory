"""
Comando para crear historias de prueba para probar el scroll infinito.
Uso: python manage.py seed_stories
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.stories.models import Story, Category
from django.utils import timezone


SAMPLE_STORIES = [
    {
        'title': 'El despertar de la inteligencia artificial',
        'excerpt': 'Un viaje fascinante por los orígenes y el futuro de la IA.',
        'content': '<h2>Los inicios</h2><p>La inteligencia artificial ha recorrido un largo camino desde sus humildes comienzos en la década de 1950. Lo que empezó como un sueño de científicos visionarios se ha convertido en una realidad que transforma cada aspecto de nuestras vidas.</p><p>Desde los primeros programas de ajedrez hasta los modelos de lenguaje que pueden mantener conversaciones coherentes, la evolución ha sido vertiginosa. Cada década ha traído avances que parecían imposibles para la generación anterior.</p><blockquote>La pregunta ya no es si las máquinas pueden pensar, sino hasta dónde llegarán.</blockquote><p>Hoy en día, la IA no es solo una herramienta tecnológica: es un catalizador de cambio social, económico y cultural que redefine lo que significa ser humano en el siglo XXI.</p>',
        'category_name': 'Tecnología',
    },
    {
        'title': 'Recuerdos de un verano en la costa',
        'excerpt': 'Reflexiones sobre el paso del tiempo y los momentos que nos definen.',
        'content': '<p>Hay veranos que se quedan grabados en la memoria como fotografías perfectas. El sonido de las olas rompiendo contra las rocas, el sabor del helado derritiéndose bajo el sol, las risas que se mezclaban con la brisa marina.</p><h2>El primer día</h2><p>Llegamos al pueblo costero un miércoles de julio. Las calles empedradas olían a jazmín y a sal. La casa que habíamos alquilado tenía las paredes blancas y las contraventanas azules, como sacada de una postal mediterránea.</p><p>Aquellos días nos enseñaron que la felicidad no está en los grandes eventos, sino en los pequeños momentos compartidos con quienes amamos.</p>',
        'category_name': 'Relatos',
    },
    {
        'title': 'Guía completa para aprender Django en 2024',
        'excerpt': 'Todo lo que necesitas saber para dominar el framework web más popular de Python.',
        'content': '<h2>¿Por qué Django?</h2><p>Django es uno de los frameworks web más completos y maduros del ecosistema Python. Con su filosofía de "baterías incluidas", permite construir aplicaciones web robustas en tiempo récord.</p><ul><li>ORM potente para bases de datos</li><li>Sistema de autenticación integrado</li><li>Panel de administración automático</li><li>Protección contra ataques comunes (CSRF, XSS, SQL Injection)</li></ul><h2>Primeros pasos</h2><p>Empezar con Django es sorprendentemente sencillo. Con apenas unas líneas de código puedes tener un servidor web funcionando con una base de datos lista para usar.</p><p>La comunidad es enorme y la documentación es considerada una de las mejores en el mundo del desarrollo web.</p>',
        'category_name': 'Tecnología',
    },
    {
        'title': 'El arte de la escritura creativa',
        'excerpt': 'Técnicas y consejos para liberar tu creatividad literaria.',
        'content': '<p>Escribir es un acto de valentía. Cada vez que ponemos palabras sobre el papel, estamos exponiendo una parte de nosotros mismos al mundo. Pero es precisamente esa vulnerabilidad la que hace que la escritura sea tan poderosa.</p><h2>Encontrar tu voz</h2><p>Cada escritor tiene una voz única. No se trata de imitar a los grandes autores, sino de descubrir tu propia forma de contar historias. Tu perspectiva es irrepetible, y eso es tu mayor fortaleza.</p><blockquote>No hay nada más terrorífico que una página en blanco, pero tampoco hay nada más emocionante que llenarla con tus palabras.</blockquote><p>La clave está en escribir todos los días, sin importar si lo que sale es bueno o malo. La práctica constante es lo que transforma a un aficionado en un artista.</p>',
        'category_name': 'Escritura',
    },
    {
        'title': 'Viaje por los mercados de Marrakech',
        'excerpt': 'Colores, aromas y experiencias en el corazón de Marruecos.',
        'content': '<p>Los zocos de Marrakech son un asalto a todos los sentidos. Desde el momento en que cruzas la puerta principal, te envuelve un torbellino de colores, sonidos y aromas que te transportan a otro mundo.</p><h2>El zoco de las especias</h2><p>Montañas de cúrcuma dorada, pimentón rojo intenso, comino que perfuma el aire... Los comerciantes te invitan a probar, a oler, a dejarte seducir por los sabores del norte de África.</p><p>Cada callejón esconde una sorpresa: un artesano trabajando el cuero, un vendedor de lámparas de latón que proyectan estrellas en las paredes, una tetera humeante de té de menta esperando ser servida.</p><h2>La plaza Jemaa el-Fna</h2><p>Al caer la noche, la plaza cobra vida propia. Cuentacuentos, músicos, acróbatas y puestos de comida transforman el espacio en un teatro a cielo abierto que hay que vivir al menos una vez en la vida.</p>',
        'category_name': 'Viajes',
    },
    {
        'title': 'Cómo la música cambia nuestro cerebro',
        'excerpt': 'La neurociencia detrás de las melodías que amamos.',
        'content': '<p>La música tiene un poder extraordinario sobre nuestro cerebro. Investigaciones recientes han demostrado que escuchar música activa prácticamente todas las áreas del cerebro simultáneamente, algo que pocas actividades humanas logran.</p><h2>El efecto dopamina</h2><p>Cuando escuchamos una canción que nos gusta, nuestro cerebro libera dopamina, el mismo neurotransmisor asociado con el placer de comer o el amor. Es por eso que la música puede provocarnos escalofríos de emoción.</p><p>Los músicos, en particular, tienen cerebros estructuralmente diferentes: mayor volumen en el cuerpo calloso, mejor conectividad neuronal y mayor capacidad de procesamiento multisensorial.</p><h2>Música y memoria</h2><p>La conexión entre música y memoria es tan fuerte que personas con Alzheimer avanzado pueden recordar canciones de su juventud con total claridad, incluso cuando han olvidado los nombres de sus seres queridos.</p>',
        'category_name': 'Ciencia',
    },
    {
        'title': 'Recetas de la abuela: cocina tradicional española',
        'excerpt': 'Platos que cuentan historias de familia y tradición.',
        'content': '<h2>La tortilla de patatas perfecta</h2><p>No hay debate más apasionado en España que si la tortilla lleva cebolla o no. En nuestra familia, la respuesta siempre ha sido clara: con cebolla, pochada lentamente hasta que se carameliza y aporta esa dulzura que hace de cada bocado una experiencia.</p><p>La receta de la abuela requiere paciencia: patatas cortadas finas, cocinadas a fuego lento en abundante aceite de oliva virgen extra, huevos de corral bien batidos y ese punto exacto de cuajado que marca la diferencia entre una tortilla buena y una memorable.</p><h2>Gazpacho andaluz</h2><p>En verano, nada supera un gazpacho bien frío. Tomates maduros, pepino, pimiento verde, un diente de ajo, pan del día anterior, vinagre de Jerez y el mejor aceite de oliva que puedas encontrar.</p>',
        'category_name': 'Cultura',
    },
    {
        'title': 'El futuro del trabajo remoto',
        'excerpt': 'Cómo la pandemia transformó para siempre nuestra forma de trabajar.',
        'content': '<p>El trabajo remoto pasó de ser una excepción a convertirse en la norma para millones de personas en todo el mundo. Lo que empezó como una medida de emergencia se ha transformado en una revolución laboral que está redefiniendo las ciudades, las relaciones profesionales y nuestra concepción del equilibrio entre vida personal y trabajo.</p><h2>Ventajas y desafíos</h2><ul><li>Mayor flexibilidad y autonomía</li><li>Eliminación del tiempo de commuting</li><li>Acceso a talento global</li><li>Riesgo de aislamiento social</li><li>Difuminación de límites trabajo-vida</li></ul><p>Las empresas que han sabido adaptarse están descubriendo que la productividad no depende de la presencia física, sino de la confianza, las herramientas adecuadas y una cultura organizacional sólida.</p>',
        'category_name': 'Tecnología',
    },
    {
        'title': 'Fotografía nocturna: capturando las estrellas',
        'excerpt': 'Técnicas para fotografiar el cielo nocturno con resultados espectaculares.',
        'content': '<p>Hay pocas experiencias más gratificantes que capturar la Vía Láctea con tu cámara. La fotografía nocturna combina técnica, paciencia y un profundo respeto por la naturaleza.</p><h2>Equipo necesario</h2><p>No necesitas el equipo más caro del mercado. Una cámara con modo manual, un objetivo luminoso (f/2.8 o más abierto), un trípode resistente y un disparador remoto son suficientes para empezar.</p><h2>La regla del 500</h2><p>Para evitar que las estrellas salgan como trazos en lugar de puntos, divide 500 entre la distancia focal de tu objetivo. El resultado es el tiempo máximo de exposición en segundos. Con un objetivo de 20mm, por ejemplo, puedes exponer hasta 25 segundos.</p><blockquote>Las mejores fotografías nocturnas se hacen en noches sin luna, lejos de la contaminación lumínica, cuando el cielo se convierte en un lienzo de estrellas.</blockquote>',
        'category_name': 'Cultura',
    },
    {
        'title': 'Meditación para principiantes',
        'excerpt': 'Una guía práctica para comenzar tu práctica de mindfulness.',
        'content': '<p>La meditación no requiere sentarse en posición de loto ni vaciar la mente por completo. Es, simplemente, la práctica de prestar atención al momento presente con curiosidad y sin juicio.</p><h2>Empezando con 5 minutos</h2><p>Siéntate cómodamente, cierra los ojos y presta atención a tu respiración. Cuando tu mente se distraiga (y lo hará, es completamente normal), simplemente nota la distracción y vuelve a la respiración. Eso es todo.</p><h2>Beneficios comprobados</h2><ul><li>Reducción del estrés y la ansiedad</li><li>Mejora de la concentración</li><li>Mayor regulación emocional</li><li>Mejor calidad del sueño</li><li>Fortalecimiento del sistema inmunológico</li></ul><p>La clave es la consistencia: es mejor meditar 5 minutos cada día que una hora una vez a la semana.</p>',
        'category_name': 'Bienestar',
    },
    {
        'title': 'Historia de los videojuegos: del Pong al metaverso',
        'excerpt': 'Un recorrido por la evolución del entretenimiento interactivo.',
        'content': '<p>En apenas 50 años, los videojuegos han pasado de ser simples píxeles rebotando en una pantalla a mundos virtuales de una complejidad asombrosa. Esta es la historia de una industria que ya supera a Hollywood y la música combinados.</p><h2>Los años dorados del arcade</h2><p>Pac-Man, Space Invaders, Donkey Kong... Los salones recreativos de los años 80 fueron la cuna de una revolución cultural. Cada máquina era un portal a un universo de posibilidades, alimentado por monedas y sueños de puntuaciones récord.</p><h2>La era de las consolas</h2><p>Nintendo, Sega, Sony, Microsoft... La guerra de consolas ha sido uno de los motores de innovación más potentes de la industria tecnológica, empujando los límites del hardware y el software en cada generación.</p><p>Hoy, con la realidad virtual y el cloud gaming, estamos al borde de una nueva revolución que difuminará las fronteras entre el mundo real y el digital.</p>',
        'category_name': 'Tecnología',
    },
    {
        'title': 'El secreto de los jardines japoneses',
        'excerpt': 'Filosofía, diseño y armonía en el arte del paisajismo nipón.',
        'content': '<p>Un jardín japonés no es simplemente un espacio verde: es una obra de arte viva que encapsula siglos de filosofía, estética y espiritualidad. Cada roca, cada rama, cada gota de agua tiene un significado y un propósito.</p><h2>Los principios fundamentales</h2><p>La asimetría, la simplicidad y la naturalidad son los tres pilares del diseño de jardines japoneses. Nada es accidental, pero todo debe parecer espontáneo, como si la naturaleza misma hubiera decidido crear esa composición perfecta.</p><h2>El jardín zen (karesansui)</h2><p>Los jardines de piedra y arena rastrillada son probablemente la expresión más pura de esta filosofía. Sin agua, sin plantas, solo piedras cuidadosamente colocadas sobre un mar de grava blanca que representa el océano infinito de la existencia.</p><blockquote>En un jardín japonés, el vacío es tan importante como la presencia. Es en los espacios vacíos donde la mente encuentra la calma.</blockquote>',
        'category_name': 'Cultura',
    },
    {
        'title': 'Aprender a cocinar: errores que todos cometemos',
        'excerpt': 'Los fallos más comunes en la cocina y cómo evitarlos.',
        'content': '<p>Todos hemos quemado algo, añadido demasiada sal o sacado un bizcocho hundido del horno. Los errores en la cocina son inevitables, pero conocerlos de antemano puede ahorrarnos muchos disgustos.</p><h2>Error #1: No leer la receta completa antes de empezar</h2><p>Es tentador empezar a cocinar mientras lees, pero esto lleva a sorpresas desagradables como descubrir que necesitas dejar marinar algo durante 4 horas cuando ya es hora de cenar.</p><h2>Error #2: Sartén fría</h2><p>Uno de los errores más comunes es no calentar suficiente la sartén antes de añadir los ingredientes. Una sartén bien caliente es la diferencia entre un filete dorado y jugoso y un trozo de carne gris y hervido.</p><h2>Error #3: Abrir el horno constantemente</h2><p>Cada vez que abres el horno, la temperatura baja entre 10 y 25 grados. Esa curiosidad por ver cómo va tu bizcocho puede ser exactamente la razón por la que se hunde.</p>',
        'category_name': 'Cultura',
    },
    {
        'title': 'La magia de los libros que nos cambiaron la vida',
        'excerpt': 'Esos libros que llegan en el momento justo y lo transforman todo.',
        'content': '<p>Hay libros que simplemente se leen, y hay libros que cambian quiénes somos. Son aquellos que llegan en el momento exacto, cuando nuestro corazón está abierto y nuestra mente preparada para recibir su mensaje.</p><h2>Lecturas que marcan</h2><p>Para algunos fue "El Principito", que nos enseñó que lo esencial es invisible a los ojos. Para otros fue "Cien años de soledad", que nos mostró que la realidad es tan fantástica como cualquier ficción. O quizás fue un libro técnico que abrió las puertas de una carrera profesional.</p><p>Lo hermoso de la lectura es que cada persona encuentra su libro transformador en un lugar diferente. No importa el género ni la complejidad: lo que importa es la conexión que se establece entre las palabras del autor y el mundo interior del lector.</p><blockquote>Un buen libro es aquel que cuando terminas de leerlo, sientes que ya no eres la misma persona que lo empezó.</blockquote>',
        'category_name': 'Escritura',
    },
    {
        'title': 'Caminando por los senderos del Camino de Santiago',
        'excerpt': 'Experiencias y reflexiones de un peregrino moderno.',
        'content': '<p>El Camino de Santiago es mucho más que una ruta de senderismo. Es un viaje interior que te confronta contigo mismo, con tus límites físicos y mentales, y con la inmensa generosidad de los desconocidos que encuentras por el camino.</p><h2>Los primeros kilómetros</h2><p>Los pies protestan, la mochila pesa más de lo que pensabas, y te preguntas por qué decidiste hacer esto. Pero entonces, al coronar una colina, el paisaje se abre ante ti: campos de cereal dorado bajo un cielo infinito, pueblos medievales de piedra dormidos entre viñedos.</p><h2>Las lecciones del camino</h2><p>Caminar durante semanas te enseña cosas que ningún libro puede transmitir: que necesitas mucho menos de lo que crees, que la felicidad está en las cosas simples, y que las mejores conversaciones surgen cuando simplemente compartes el camino con otro peregrino.</p><p>¡Buen Camino!</p>',
        'category_name': 'Viajes',
    },
]


class Command(BaseCommand):
    help = 'Crea historias de prueba para probar el scroll infinito y otras funcionalidades'

    def handle(self, *args, **options):
        # Get or create an admin user
        admin_user = User.objects.filter(is_staff=True).first()
        if not admin_user:
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@weekstory.local',
                password='admin1234'
            )
            self.stdout.write(self.style.WARNING(
                f'Creado usuario admin: admin / admin1234'
            ))

        created_count = 0
        for story_data in SAMPLE_STORIES:
            # Create category if needed
            cat_name = story_data.pop('category_name')
            from django.utils.text import slugify
            category, _ = Category.objects.get_or_create(
                slug=slugify(cat_name),
                defaults={'name': cat_name}
            )

            # Check if story already exists
            if not Story.objects.filter(title=story_data['title']).exists():
                Story.objects.create(
                    user=admin_user,
                    category=category,
                    status='published',
                    published_at=timezone.now(),
                    extraction_status='completed',
                    **story_data
                )
                created_count += 1
                self.stdout.write(f'  ✓ "{story_data["title"]}"')

        self.stdout.write(self.style.SUCCESS(
            f'\n¡Listo! {created_count} historias creadas. Total: {Story.objects.count()} historias.'
        ))
