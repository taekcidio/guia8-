# La Tiendita — Guía 8

Aplicación universitaria de tienda en línea construida con Python, SQLite, HTML, CSS y JavaScript. Permite consultar productos, registrar usuarios y crear pedidos que actualizan el inventario.

Los pedidos son simulados: no se realizan cobros ni se procesan pagos. La aplicación se ejecuta localmente en un contenedor Docker; la arquitectura en la nube es una propuesta académica, no un despliegue en un proveedor cloud.

## Estructura

- `app/server.py`: servidor HTTP y API con persistencia SQLite.
- `app/index.html`: estructura de la tienda.
- `app/static/css/` y `app/static/js/`: estilos y comportamiento del navegador.
- `app/static/images/productos/`: fotografías guardadas localmente para servirlas también dentro de Docker.
- `data/comercio.db`: base SQLite para ejecución local fuera de Docker.
- `tests/`: pruebas automáticas del registro, pedidos y existencias.
- `Dockerfile` y `compose.yaml`: imagen y ejecución local con volumen persistente.

## Ejecutar con Docker

1. Abre la carpeta `guia8` en Visual Studio Code e inicia Docker Desktop.
2. Desde una terminal en esa carpeta, reconstruye e inicia el servicio:

   ```powershell
   docker compose up --build -d
   ```

3. Abre [http://localhost:8080](http://localhost:8080).
4. Comprueba el contenedor y su healthcheck:

   ```powershell
   docker compose ps
   Invoke-RestMethod http://localhost:8080/api/health
   ```

Para ver los registros: `docker compose logs -f`. Para detener el servicio sin borrar los datos: `docker compose down`. Los pedidos y usuarios de Docker se conservan en el volumen `demo_data`; no uses `docker compose down -v` si deseas conservarlos.

El puerto del contenedor se publica solo en `127.0.0.1:8080`, y el servidor escucha en `0.0.0.0` dentro del contenedor.

## Ejecutar sin Docker

Con Python 3 instalado, desde la raíz del proyecto:

```powershell
python app/server.py
```

La aplicación estará en [http://localhost:8080](http://localhost:8080). En este modo la base se guarda en `data/comercio.db`.

## Pruebas

```powershell
python -m unittest discover -s tests -v
```

Las pruebas usan una base temporal y no modifican la base de datos real del proyecto.

## Fotografías

Las fotos del catálogo se guardan en `app/static/images/productos/`, de modo que no se necesitan conexiones externas para mostrarlas. Las fotos de calzado, botella y mochila provienen de Unsplash y se usan conforme a la [Licencia de Unsplash](https://unsplash.com/license):

- [Tenis para running](https://images.unsplash.com/photo-1460353581641-37baddab0fa2)
- [Botella térmica](https://images.unsplash.com/photo-1602143407151-7111542de6e8)
- [Mochila deportiva](https://images.unsplash.com/photo-1553062407-98eeb64c6a62)

La foto de entrenamiento con banda es de [Nenad Stojkovic](https://www.flickr.com/photos/nenadstojkovic/49250556071/), compartida en [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Attractive_young_woman_have_exercise_with_tape_in_the_gym.jpg) con licencia [CC BY 2.0](https://creativecommons.org/licenses/by/2.0/).

## Contexto académico

Proyecto de la Universidad Manuela Beltrán para la actividad de computación en la nube. Demuestra una aplicación contenerizada de ejecución local y propone una arquitectura cloud; no está desplegada en AWS ni en otro proveedor.
