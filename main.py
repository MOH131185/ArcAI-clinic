import os
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from extract_images import extract_images
from clip_utils import embed_images, load_embeddings, search_embeddings

app = FastAPI()

# 1) Serve our minimal frontend UI under /static
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# 2) Serve the rendered portfolio page JPGs under /portfolio_pages
app.mount(
    "/portfolio_pages",
    StaticFiles(directory="static/portfolio_pages"),
    name="pages",
)

@app.get("/")
def homepage():
    return FileResponse("frontend/index.html")


@app.post("/embed-portfolio")
async def embed_portfolio(file: UploadFile = File(...)):
    # 1️⃣ Save the incoming PDF
    upload_dir = "portfolio_uploads"
    os.makedirs(upload_dir, exist_ok=True)
    pdf_path = os.path.join(upload_dir, file.filename)
    with open(pdf_path, "wb") as f:
        f.write(await file.read())

    # 2️⃣ Convert PDF → JPG pages
    image_dir = "static/portfolio_pages"
    os.makedirs(image_dir, exist_ok=True)
    pages = extract_images(pdf_path, image_dir)
    if not pages:
        raise HTTPException(500, "Failed to extract any pages")

    # 3️⃣ Embed all pages & write out static/clip_embeddings.json
    embeddings_file = "static/clip_embeddings.json"
    processed, skipped = embed_images(image_dir, embeddings_file)

    return JSONResponse({
        "message": "Embeddings saved",
        "processed": processed,
        "skipped": skipped
    })


@app.get("/search")
def search(query: str, k: int = 5):
    # load up your saved embeddings & run the CLIP search
    embeddings = load_embeddings("static/clip_embeddings.json")
    results = search_embeddings(embeddings, query, k)
    return {"query": query, "results": results}
