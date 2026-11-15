"""QoreX — SPHEREx Motion Explorer · Modal.com deployment.

Free-tier hosting (no card): ASGI web endpoint with a stable
<workspace>--qorex.modal.run URL. The workbench FastAPI app is served
unchanged; all data still comes live from NASA/IPAC IRSA.

Deploy:    modal deploy modal_app.py
"""

import modal

app = modal.App("qorex")

image = (
    modal.Image.debian_slim(python_version="3.12")
    .add_local_file("requirements.txt", "/root/requirements.txt")
    .pip_install_from_requirements("/root/requirements.txt")
    .add_local_dir("backend", "/root/backend")
    .add_local_dir("frontend", "/root/frontend")
)


@app.function(
    image=image,
    # Scale-to-zero: the free signup credit (~$1, no card) buys ~15-20
    # container-hours of ACTIVE use — enough for a full judging week of
    # bursts. First request after idle pays a ~10-20s cold boot.
    cpu=0.5,
    memory=768,
    timeout=600,
)
@modal.asgi_app()
def qorex():
    from backend.app import app as fastapi_app

    return fastapi_app
