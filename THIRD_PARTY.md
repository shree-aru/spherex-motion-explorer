# Third-party data, tools and attribution

This repository's HTML, CSS, JavaScript, and backend orchestration are original for this prototype. It **uses** established, credited astronomical software and public archives rather than copying their interfaces or making up astronomical measurements.

- **SPHEREx/IRSA data:** NASA / JPL-Caltech / IPAC; follow official IRSA acknowledgements, user guidance and release documentation. NASA mission names are used descriptively; this is not a NASA-sponsored or NASA-operated UI.
- **Aladin Lite v3:** Centre de Données astronomiques de Strasbourg (CDS); loaded from the official CDN for optional reference-atlas functionality. Its native identity and attribution should be kept visible. Confirm the precise version's license/usage terms before public release.
- **Astropy**, **reproject**, **NumPy**, **Pillow**, **FastAPI**, **httpx**, and **Uvicorn**: respective authors and licensed dependencies; consult their current LICENSE files before distribution.
- **DSS2 reference sky survey:** third-party HiPS survey in Aladin; do not relabel as SPHEREx imagery. Maintain that survey's credit display and verify image usage terms.
- **SIMBAD:** CDS, Strasbourg astronomical database. Object positions and proper motions are catalogue-derived; catalog epochs should be retained.

UI uses system fonts, self-authored CSS geometry, and plain text icons/lines; no generated space-themed illustrations or third-party dashboard templates are embedded.

## Dataset-level citations used in the preview

- QR3: [DOI 10.26131/IRSA662](https://doi.org/10.26131/IRSA662).
- QR2: [DOI 10.26131/IRSA652](https://doi.org/10.26131/IRSA652).
- Official collection identifiers and SIA usage: [Caltech/IPAC archive guide (2026)](https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-access/).

Retain the official SPHEREx acknowledgement in published work. No redistribution or guarantee of third-party catalogue/image licensing is asserted by this prototype.
