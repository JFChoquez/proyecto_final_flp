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
```text
├── client/
│   ├── client.py       # Aplicación Tkinter (todas las pantallas).
│   ├── net_client.py   # Helper de red usado por el cliente.
│   ├── protocol.py     # Framing de mensajes (longitud + JSON) para sockets.
│   ├── theme.py        # Paleta de colores y estilos ttk (Material Design).
│   └── venv/           # Entorno virtual de Python.
├── README.md           
└── server/
    ├── cuidadores.db   # Base de datos SQLite (se crea sola al iniciar).
    ├── database.py     # Esquema SQLite y acceso a datos.
    ├── protocol.py     # Framing de mensajes (longitud + JSON) para sockets.
    └── server.py       # Servidor TCP con hilos, un hilo por cliente conectado.
```

## Notas
- El cliente por defecto se conecta al servidor de prueba, si deseas ejecutarlo en local cambia la variable HOST en los archivos protocol.py
- Las miniaturas de mascotas se leen del disco local del cliente asumiendo que comparte la carpeta `storage/` con el servidor (ej. ambos en la misma máquina). En un despliegue real en varias máquinas, habría que añadir un endpoint de descarga de imagen.

