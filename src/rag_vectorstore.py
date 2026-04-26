"""
Módulo RAG - Vector Store con ChromaDB
Usa sentence-transformers para embeddings (sin Ollama)
Singleton para evitar recargas
"""

import os
from pathlib import Path
from typing import List, Optional
import chromadb

from src.rag_extractor import (
    extraer_texto_pdf, obtener_documentos, chunkify, obtener_metadata
)


CHROMA_DIR = Path(__file__).parent.parent / "data" / "chroma"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

_embedder_instance = None


def get_embedder(model_name: str = EMBEDDING_MODEL):
    """Singleton del embedder - reuse modelo"""
    global _embedder_instance
    if _embedder_instance is None:
        from sentence_transformers import SentenceTransformer
        print(f"📥 Cargando modelo: {model_name}")
        _embedder_instance = SentenceTransformer(model_name)
        print("✅ Modelo cargado")
    return _embedder_instance


class VectorStore:
    def __init__(self, collection_name: str = "rebt_docs"):
        self.collection_name = collection_name
        self.client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self.collection = None
        self._init_collection()
    
    def _init_collection(self):
        try:
            self.collection = self.client.get_collection(self.collection_name)
        except:
            self.collection = self.client.create_collection(
                self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
    
    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        embedder = get_embedder()
        embeddings = embedder.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings.tolist()
    
    def indexar_documento(self, ruta: str, tipo: str) -> int:
        print(f"📄 Indexando: {os.path.basename(ruta)}")
        
        texto = extraer_texto_pdf(ruta)
        if not texto.strip():
            print("  ⚠️ Sin texto extraído")
            return 0
        
        chunks = chunkify(texto, chunk_size=800, overlap=100)
        print(f"  📝 {len(chunks)} chunks")
        
        if not chunks:
            return 0
        
        embeddings = self._get_embeddings(chunks)
        metadatos = [obtener_metadata(ruta, tipo) for _ in chunks]
        ids = [f"{os.path.basename(ruta)}_{i}" for i in range(len(chunks))]
        
        self.collection.add(
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatos,
            ids=ids
        )
        
        print(f"  ✅ {len(chunks)} chunks indexados")
        return len(chunks)
    
    def indexar_todos(self) -> int:
        total = 0
        docs = obtener_documentos()
        
        for ruta, tipo in docs:
            try:
                total += self.indexar_documento(ruta, tipo)
            except Exception as e:
                print(f"  ❌ Error: {e}")
        
        print(f"\n📊 Total indexado: {total} chunks")
        return total
    
    def buscar(self, query: str, n_resultados: int = 5) -> List[dict]:
        embedder = get_embedder()
        query_embedding = embedder.encode([query], convert_to_numpy=True, show_progress_bar=False)
        
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_resultados
        )
        
        docs = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                docs.append({
                    "texto": doc,
                    "fuente": results["metadatas"][0][i].get("source", "desconocido"),
                    "tipo": results["metadatas"][0][i].get("type", "desconocido"),
                    "similitud": 1 - results["distances"][0][i]
                })
        
        return docs
    
    def buscar_por_tipo(self, query: str, tipo: str, n_resultados: int = 5) -> List[dict]:
        results = self.buscar(query, n_resultados * 2)
        return [r for r in results if r.get("tipo") == tipo][:n_resultados]
    
    def limpiar(self):
        self.client.delete_collection(self.collection_name)
        self._init_collection()
        print("🧹 Colección limpiada")


def init_vectorstore() -> VectorStore:
    return VectorStore()


if __name__ == "__main__":
    print("🗂️ Vector Store REBT (optimizado)")
    print("=" * 50)
    
    store = init_vectorstore()
    
    print("\n1. Indexar documentos")
    print("2. Buscar")
    print("3. Limpiar")
    
    opcion = input("\nOpción: ").strip()
    
    if opcion == "1":
        store.limpiar()
        store.indexar_todos()
    elif opcion == "2":
        query = input("Búsqueda: ").strip()
        if query:
            results = store.buscar(query)
            for r in results:
                print(f"\n[{r['fuente']}] ({r['tipo']})")
                print(f"  {r['texto'][:200]}...")
    elif opcion == "3":
        store.limpiar()