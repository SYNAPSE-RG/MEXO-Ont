# MEXO — WIDOCO + GitHub Pages Package

This package prepares the `SYNAPSE-RG/MEXO-Ont` repository to automatically
generate and publish the MEXO documentation using **WIDOCO 1.4.25**.

## Structure

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

`mexo-publication.ttl` combines the OWL ontology and the SKOS taxonomy so that
WIDOCO documents both components on a single website.

## 1. Add the files to the repository

On macOS/Linux:

```bash
git clone https://github.com/SYNAPSE-RG/MEXO-Ont.git
cd MEXO-Ont

# Copy the contents of this package into this directory,
# preserving exactly the structure shown above.
```

If you already have a local clone:

```bash
cd MEXO-Ont
git pull origin main
```

## 2. Generate the documentation locally

Recommended requirement: Docker Desktop.

```bash
chmod +x scripts/build-widoco.sh
./scripts/build-widoco.sh
```

The script uses the official image:

```text
ghcr.io/dgarijo/widoco:v1.4.25
```

The output is generated in:

```text
site/
```

To review the documentation:

```bash
python3 -m http.server 8000 --directory site
```

Then open:

```text
http://localhost:8000/
```

The WIDOCO execution includes:

- automatic documentation of classes and properties;
- vocabulary metadata;
- the SKOS taxonomy within the publication graph;
- WebVOWL;
- a unified HTML page (`-uniteSections`);
- links to the source code repository.

## 3. Push the changes

```bash
git add ontology widoco scripts .github site
git commit -m "Add WIDOCO documentation and GitHub Pages workflow"
git push origin main
```

## 4. Enable GitHub Pages

On GitHub:

1. Open `SYNAPSE-RG/MEXO-Ont`.
2. Go to **Settings**.
3. Select **Pages**.
4. Under **Build and deployment**, select **Source: GitHub Actions**.
5. Save the settings if GitHub displays a confirmation option.
6. Open the **Actions** tab and select `Publish WIDOCO documentation`.
7. The action will also run automatically when `ontology/`, `widoco/`, the
   build script, or the workflow is modified.

## 5. Expected URL

Once deployment is complete, the documentation should be available at:

```text
https://synapse-rg.github.io/MEXO-Ont/
```

GitHub will display the exact URL under **Settings > Pages** and in the
deployment job.

## 6. Recommended maintenance workflow

For each new version:

1. Update `ontology/mexo-ontology-v5.2.0.ttl` or create the file for the new version.
2. Update `ontology/mexo-taxonomy-w3id.ttl` if the taxonomy changes.
3. Regenerate `ontology/mexo-publication.ttl` if the sources remain separate.
4. Update `widoco/config.properties` (`ontologyRevisionNumber`,
   `thisVersionURI`, `dateModified`, etc.).
5. Run `git commit` and `git push`.
6. GitHub Actions will automatically regenerate and republish the WIDOCO documentation.

## 7. Relationship with w3id.org

The canonical namespace used by this package is:

```text
https://w3id.org/mexo/
```

GitHub Pages serves as the documentation website, while `w3id.org` serves as
the persistent identifier. The `widoco/w3id-htaccess-example.txt` file contains
an example for redirecting HTML requests to GitHub Pages and Turtle requests to
the RDF file in the repository.

Before replacing an existing configuration on w3id.org, carefully merge these
rules with the `.htaccess` file already approved for MEXO.

## Note on the prepared sources

The publication ontology incorporates the persistent namespace
`https://w3id.org/mexo/` and the structural changes documented for MEXO 5.2.0.
The provided taxonomy is conceptually preserved and normalized to the same
namespace for joint publication.

## Files that should not be edited manually

The contents of `site/` are generated artifacts. The source of truth should
remain `ontology/` + `widoco/config.properties`. On GitHub, the workflow
generates `site/` from scratch during each deployment.
