# Score Split OMR
Audiveris 5.11.0 wrapper for Score Split.

- GET /health
- POST /v1/recognize — multipart/form-data field `file`, PDF/JPG/PNG, max 20 MB.

Runs Audiveris in batch mode and returns MusicXML/MXL. Intended for Docker deployment on Render.

Audiveris is AGPL-3.0 licensed: https://github.com/Audiveris/audiveris
