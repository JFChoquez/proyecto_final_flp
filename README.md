# Red Inteligente de Cuidadores de Mascotas

## Requisitos
```
pip install pillow
```
Pillow es opcional: si no está instalada, la app funciona igual pero no muestra las miniaturas de las fotos.

## Ejecución
1. Iniciar el servidor (deja esta terminal abierta):
```
python3 server.py
```
2. En otra terminal, iniciar uno o varios clientes:
```
python3 client.py
```

## Estructura
- `protocol.py` — framing de mensajes (longitud + JSON) para los sockets.
- `database.py` — esquema SQLite y acceso a datos.
- `server.py` — servidor TCP con hilos, un hilo por cliente conectado.
- `net_client.py` — helper de red usado por el cliente.
- `theme.py` — paleta de colores y estilos ttk (Material Design).
- `client.py` — aplicación Tkinter (todas las pantallas).
- `storage/mascotas/` — fotos de mascotas guardadas por el servidor.
- `cuidadores.db` — base de datos SQLite (se crea sola al iniciar el servidor).

## Refrescar la conexión / los datos
Si la app se queda "colgada" o los datos no se ven actualizados (por ejemplo,
después de que otro usuario acepta o cancela un servicio), presiona **F5**
(o Ctrl+R) en cualquier pantalla para volver a consultar al servidor y
redibujar la vista actual. También hay un botón **"⟳ Actualizar (F5)"**
visible en la barra superior de cada pantalla para hacer lo mismo con un clic.

## Datos que ahora captura el sistema
**Dueños de mascotas**, además de sus datos personales, tipo/raza/edad/necesidades
de la mascota, ahora también indican al contratar un servicio:
- Horario del servicio (además de la fecha y la duración)
- Ubicación donde se prestará el servicio
- Presupuesto (opcional)

**Cuidadores**, en la pantalla "Mi Experiencia" (o desde "Mi Perfil"), además de
su descripción y experiencia, ahora registran:
- Tarifa por hora (S/)
- Certificaciones (veterinaria, adiestramiento, primeros auxilios, etc.)
- Disponibilidad (horarios en que trabajan)
- Zona(s) de trabajo (pueden marcar varios distritos, no solo el suyo)

## Perfil del cuidador (vista del dueño)
Al abrir "Ver perfil" de un cuidador, ahora se muestra:
- Tarifa, disponibilidad, zona de trabajo y certificaciones
- Un precio estimado calculado automáticamente con la tarifa y la duración indicada
- Una lista de **reseñas y comentarios** (estilo tienda de aplicaciones): quién
  calificó, cuántas estrellas, el comentario escrito y la fecha
- El formulario de contratación pide horario, ubicación del servicio y presupuesto,
  y al enviarse muestra un número de confirmación de servicio (contrato).

Los cuidadores en el panel del dueño se listan ordenados por **ranking de
confianza** (mejor calificación promedio y más reseñas primero).

## Nuevas tablas en SQLite
- `Incidentes` — reportes de incidentes ligados a un contrato (gravedad, descripción, fecha).
  Tanto el dueño como el cuidador pueden reportar uno desde su respectiva pantalla de solicitudes.
- `Pagos` — registro de pagos por contrato (monto, método, estado, fecha). Se genera
  automáticamente al calificar un servicio si se indicó un presupuesto.
- `Contratos_Servicios` ahora también guarda `horario`, `ubicacion_servicio`, `presupuesto`,
  `comentario` (texto de la reseña) y `fecha_calificacion`.
- El estado de un contrato ahora puede ser `pendiente`, `aceptado`, `rechazado`,
  `cancelado` (el dueño o el cuidador pueden cancelar) o `finalizado`.
- Las bases de datos `cuidadores.db` creadas con una versión anterior se actualizan
  solas: `init_db()` agrega las columnas nuevas sin borrar datos existentes.

## Notas
- Cliente y servidor deben ejecutarse en la misma máquina o red; ajusta `HOST` en `protocol.py` si el servidor corre en otra IP.
- Las miniaturas de mascotas se leen del disco local del cliente asumiendo que comparte la carpeta `storage/` con el servidor (ej. ambos en la misma máquina). En un despliegue real en varias máquinas, habría que añadir un endpoint de descarga de imagen.
