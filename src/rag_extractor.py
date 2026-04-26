"""
Módulo RAG para REBT
Extracción de texto de PDFs y embeddings con ChromaDB
"""

import os
from pathlib import Path
from typing import List, Tuple
import pypdf
from pypdf import PdfReader


DOCS_DIR = Path(__file__).parent.parent
NORMATIVA_DIR = DOCS_DIR / "normativa"
EJERCICIOS_DIR = DOCS_DIR / "ejercicios"
PROYECTOS_DIR = DOCS_DIR / "proyectos"
CHROMA_DIR = DOCS_DIR / "data" / "chroma"


def extraer_texto_pdf(ruta_pdf: str) -> str:
    """Extrae texto de un PDF"""
    try:
        reader = PdfReader(ruta_pdf)
        texto = ""
        for page in reader.pages:
            texto += page.extract_text() + "\n"
        return texto
    except Exception as e:
        print(f"Error extrayendo {ruta_pdf}: {e}")
        return ""


def listar_pdfs(directorio: Path) -> List[Path]:
    """Lista todos los PDFs en un directorio"""
    return list(directorio.glob("*.pdf"))


def obtener_documentos() -> List[Tuple[str, str]]:
    """Obtiene todos los documentos indexables"""
    docs = []
    
    # Normativa
    for pdf in listar_pdfs(NORMATIVA_DIR):
        docs.append((str(pdf), "normativa"))
    
    # Ejercicios
    for pdf in listar_pdfs(EJERCICIOS_DIR):
        docs.append((str(pdf), "ejercicios"))
    
    # Proyectos
    if PROYECTOS_DIR.exists():
        for pdf in listar_pdfs(PROYECTOS_DIR):
            docs.append((str(pdf), "proyecto"))
    
    return docs


def chunkify(texto: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """Divide texto en chunks"""
    chunks = []
    start = 0
    texto_len = len(texto)
    
    while start < texto_len:
        end = start + chunk_size
        chunk = texto[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap
    
    return chunks


def obtener_metadata(ruta: str, tipo: str) -> dict:
    """Obtiene metadatos del documento"""
    filename = os.path.basename(ruta)
    return {
        "source": filename,
        "type": tipo,
        "path": ruta
    }


if __name__ == "__main__":
    print("📚 Documentos REBT")
    print("=" * 50)
    
    docs = obtener_documentos()
    for ruta, tipo in docs:
        print(f"[{tipo.upper()}] {os.path.basename(ruta)}")
    
    print(f"\nTotal: {len(docs)} documentos")
    
    print("\n🔍 Extrayendo texto de muestra...")
    if docs:
        ruta, tipo = docs[0]
        texto = extraer_texto_pdf(ruta)
        print(f"Páginas extraídas: {len(texto) // 500}")
        print(f"Caracteres: {len(texto)}")