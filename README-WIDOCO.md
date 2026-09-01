# MEXO — paquete WIDOCO + GitHub Pages

Este paquete deja preparado el repositorio `SYNAPSE-RG/MEXO-Ont` para generar
y publicar automáticamente la documentación de MEXO con **WIDOCO 1.4.25**.

## Estructura

```text
MEXO-Ont/
├── ontology/
│   ├── mexo-ontology-v5.2.0.ttl
│   ├── mexo-taxonomy-w3id.ttl
│   └── mexo-publication.ttl
├── widoco/
│   ├── config.properties
│   └── w3id-htaccess-example.txt
├── scripts/
│   └── build-widoco.sh
├── .github/
│   └── workflows/
│       └── publish-widoco.yml
└── site/
    └── .gitkeep
```

`mexo-publication.ttl` combina la ontología OWL y la taxonomía SKOS para que
WIDOCO documente ambos componentes en un solo sitio.

## 1. Integrar los archivos al repositorio

Desde macOS/Linux:

```bash
git clone https://github.com/SYNAPSE-RG/MEXO-Ont.git
cd MEXO-Ont

# Copie dentro de este directorio el contenido de este paquete,
# conservando exactamente la estructura indicada arriba.
```

Si ya tiene un clon local:

```bash
cd MEXO-Ont
git pull origin main
```

## 2. Generar la documentación localmente

Requisito recomendado: Docker Desktop.

```bash
chmod +x scripts/build-widoco.sh
./scripts/build-widoco.sh
```

El script usa la imagen oficial:

```text
ghcr.io/dgarijo/widoco:v1.4.25
```

La salida se genera en:

```text
site/
```

Para revisar la documentación:

```bash
python3 -m http.server 8000 --directory site
```

Después abra:

```text
http://localhost:8000/
```

La ejecución de WIDOCO incluye:

- documentación automática de clases y propiedades;
- metadatos del vocabulario;
- taxonomía SKOS dentro del grafo de publicación;
- WebVOWL;
- una página HTML unificada (`-uniteSections`);
- enlaces al repositorio del código.

## 3. Subir los cambios

```bash
git add ontology widoco scripts .github site
git commit -m "Add WIDOCO documentation and GitHub Pages workflow"
git push origin main
```

## 4. Activar GitHub Pages

En GitHub:

1. Abra `SYNAPSE-RG/MEXO-Ont`.
2. Entre a **Settings**.
3. Seleccione **Pages**.
4. En **Build and deployment**, seleccione **Source: GitHub Actions**.
5. Guarde si GitHub muestra una opción de confirmación.
6. Abra la pestaña **Actions** y seleccione `Publish WIDOCO documentation`.
7. La acción también se ejecutará automáticamente al modificar `ontology/`,
   `widoco/`, el script de compilación o el workflow.

## 5. URL esperada

Cuando el deployment termine, la documentación debería quedar accesible en:

```text
https://synapse-rg.github.io/MEXO-Ont/
```

GitHub mostrará la URL exacta en **Settings > Pages** y también en el job de
deployment.

## 6. Flujo de mantenimiento recomendado

En cada nueva versión:

1. Actualice `ontology/mexo-ontology-v5.2.0.ttl` o cree el archivo de la nueva versión.
2. Actualice `ontology/mexo-taxonomy-w3id.ttl` si cambia la taxonomía.
3. Regenerar `ontology/mexo-publication.ttl` si se mantienen fuentes separadas.
4. Actualice `widoco/config.properties` (`ontologyRevisionNumber`,
   `thisVersionURI`, `dateModified`, etc.).
5. Haga `git commit` y `git push`.
6. GitHub Actions regenerará y republicará WIDOCO automáticamente.

## 7. Relación con w3id.org

El namespace canónico usado por este paquete es:

```text
https://w3id.org/mexo/
```

GitHub Pages funciona como sitio de documentación, mientras que `w3id.org`
funciona como identificador persistente. El archivo
`widoco/w3id-htaccess-example.txt` contiene un ejemplo para redirigir solicitudes
HTML a GitHub Pages y solicitudes Turtle al archivo RDF del repositorio.

Antes de sustituir una configuración existente en w3id.org, combine cuidadosamente
estas reglas con el `.htaccess` ya aprobado para MEXO.

## Nota sobre las fuentes preparadas

La ontología de publicación incorpora el namespace persistente
`https://w3id.org/mexo/` y los cambios estructurales documentados para MEXO 5.2.0.
La taxonomía suministrada se conserva conceptualmente y se normaliza al mismo
namespace para la publicación conjunta.

## Archivos que no deben editarse manualmente

El contenido de `site/` es un artefacto generado. La fuente de verdad debe seguir
siendo `ontology/` + `widoco/config.properties`. En GitHub, el workflow genera
`site/` desde cero durante cada deployment.
