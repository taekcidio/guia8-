[README.md](https://github.com/user-attachments/files/34579184/README.md)
# La Tiendita 🛍️

**Guía 8 · Computación en la nube**

La Tiendita es una aplicación web de comercio electrónico desarrollada como práctica universitaria. Permite consultar productos deportivos, buscar por nombre, filtrar por categoría, registrar usuarios y realizar pedidos de prueba. Cuando se registra un pedido, el sistema comprueba las existencias y actualiza el inventario.

El proyecto se ejecuta **localmente con Docker** y guarda la información en **SQLite**. No procesa pagos reales ni está publicado en un proveedor de nube; el despliegue cloud se presenta como propuesta en el informe.

## ¿Qué se puede hacer?

- Consultar un catálogo con fotografías, descripciones, precios en pesos colombianos y unidades disponibles.
- Buscar productos por nombre y filtrarlos por categoría.
- Registrar usuarios con nombre y correo electrónico.
- Crear pedidos de prueba y consultar su historial.
- Actualizar el inventario al registrar un pedido y evitar pedidos sin existencias suficientes.
- Comprobar el estado del servicio y ejecutar pruebas automatizadas.

## Tecnologías

| Parte | Tecnología |
| --- | --- |
| Interfaz | HTML, CSS y JavaScript |
| Servidor y API | Python 3 |
| Base de datos | SQLite |
| Contenerización | Docker y Docker Compose |
| Pruebas | `unittest` de Python |

## Organización del proyecto

```text
guia8/
├── app/
│   ├── index.html
│   ├── server.py
│   └── static/
│       ├── css/style.css
│       ├── js/main.js
│       └── images/productos/
├── data/                  # Base de datos local (no publicar datos personales)
├── evidencias/            # Resultados y capturas de pruebas
├── tests/test_demo.py
├── Dockerfile
├── compose.yaml
└── README.md
```

## Cómo ejecutar el proyecto

### Opción 1: con Docker (recomendada)

Necesitas **Docker Desktop** instalado y funcionando.

1. Descarga o clona el repositorio y abre la carpeta `guia8` en VS Code.
2. Abre una terminal dentro de esa carpeta y ejecuta:

   ```powershell
   docker compose up --build -d
   ```

3. Entra desde el navegador a **http://localhost:8080**.
4. Comprueba que el contenedor esté en ejecución:

   ```powershell
   docker compose ps
   ```

Para consultar los registros:

```powershell
docker compose logs --tail=50
```

Para detener la aplicación sin eliminar sus datos:

```powershell
docker compose down
```

> Docker conserva la base de datos en un volumen. Evita `docker compose down -v` si quieres mantener los usuarios y pedidos registrados. La aplicación publica el puerto 8080 únicamente en tu propio computador.

### Opción 2: sin Docker

Con Python 3 instalado, desde la carpeta raíz:

```powershell
python app/server.py
```

Después entra a **http://localhost:8080**. En esta modalidad, la base de datos se guarda en `data/comercio.db`.

## Pruebas

En una terminal, ejecuta:

```powershell
python -m unittest discover -s tests -v
```

En la última validación del proyecto se ejecutaron **9 pruebas automatizadas**, todas satisfactorias. Cubren el registro de usuarios, validaciones, creación de pedidos, existencias e inventario. Las pruebas utilizan una base temporal para no alterar los datos de la aplicación.

## Evidencias de funcionamiento

Durante la práctica se verificaron el catálogo con fotografías, la búsqueda, los filtros por categoría, el registro de usuarios, la creación de pedidos, los cambios de inventario y la ejecución del contenedor Docker. Las capturas y resultados se documentan en el informe de la actividad.

## Alcance y limitaciones

Esta versión es un **prototipo académico**. Los pedidos se registran de forma simulada: no se realizan cobros, no existe una pasarela de pagos y no se solicita información bancaria. La aplicación usa una base SQLite local y una sola instancia de servidor; no representa por sí misma una arquitectura productiva con alta disponibilidad, escalado automático o autenticación empresarial.

## Créditos de las imágenes

Las fotografías del catálogo se guardan en el proyecto para que la tienda pueda mostrarlas sin depender de enlaces externos.

- [Tenis para running](https://images.unsplash.com/photo-1460353581641-37baddab0fa2), [botella térmica](https://images.unsplash.com/photo-1602143407151-7111542de6e8) y [mochila deportiva](https://images.unsplash.com/photo-1553062407-98eeb64c6a62): Unsplash ([licencia](https://unsplash.com/license)).
- Fotografía de banda de resistencia: [Nenad Stojkovic, vía Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Attractive_young_woman_have_exercise_with_tape_in_the_gym.jpg), licencia [CC BY 2.0](https://creativecommons.org/licenses/by/2.0/).

---

**Universidad Manuela Beltrán · Práctica de computación en la nube**
