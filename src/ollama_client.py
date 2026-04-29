"""
Cliente REBT RAG con Ollama local
Búsquedas en documentos normativa y ejercicios + generación con Ollama
"""

import requests
from typing import List, Dict, Optional
from src.rag_vectorstore import VectorStore


OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen3-coder:30b"

SYSTEM_PROMPT = """Eres un asistente especializado en el Reglamento Electrotécnico de Baja Tensión (REBT) de España.
Respondes preguntas basándote únicamente en la información proporcionada en el contexto.
Si la información no está en el contexto, indicas que no encuentras datos al respecto.
Estructura tus respuestas de forma clara, técnica y profesional."""


class REBT_Search:
    def __init__(self):
        from src.rag_vectorstore import VectorStore
        self.vectorstore = VectorStore()
        self.ollama_url = OLLAMA_URL
        self.model = OLLAMA_MODEL
    
    def buscar(self, query: str, n_resultados: int = 5) -> List[dict]:
        return self.vectorstore.buscar(query, n_resultados)
    
    def buscar_normativa(self, query: str, n_resultados: int = 5) -> List[dict]:
        return self.vectorstore.buscar_por_tipo(query, "normativa", n_resultados)
    
    def buscar_ejercicios(self, query: str, n_resultados: int = 5) -> List[dict]:
        return self.vectorstore.buscar_por_tipo(query, "ejercicios", n_resultados)
    
    def buscar_proyectos(self, query: str, n_resultados: int = 5) -> List[dict]:
        return self.vectorstore.buscar_por_tipo(query, "proyecto", n_resultados)
    
    def _call_ollama(self, prompt: str, context: str) -> str:
        """Llama a Ollama para generar respuesta con contexto usando /api/generate"""
        try:
            full_prompt = f"{SYSTEM_PROMPT}\n\nContexto:\n{context}\n\nPregunta: {prompt}\n\nRespuesta:"
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {"temperature": 0.1}
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "Error: respuesta vacía")
            else:
                return f"Error: Ollama devolvió status {response.status_code}"
        except requests.exceptions.ConnectionError:
            return "Error: No se puede conectar a Ollama. ¿Está corriendo en localhost:11434?"
        except Exception as e:
            return f"Error llamando a Ollama: {str(e)}"
    
    def responder(self, query: str, n_resultados: int = 5) -> str:
        """Busca en RAG y genera respuesta con Ollama"""
        results = self.buscar(query, n_resultados)
        
        if not results:
            return "No he encontrado información relevante en los documentos."
        
        # Construir contexto con los resultados más relevantes
        context_parts = []
        for i, r in enumerate(results[:3], 1):
            context_parts.append(f"[Fuente {i}: {r['fuente']} - {r['tipo']}]\n{r['texto']}")
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Generar respuesta con Ollama
        return self._call_ollama(query, context)
    
    def responder_con_fuentes(self, query: str, n_resultados: int = 5) -> Dict:
        """Devuelve respuesta y fuentes por separado"""
        results = self.buscar(query, n_resultados)
        
        if not results:
            return {
                "respuesta": "No he encontrado información relevante.",
                "fuentes": []
            }
        
        context_parts = []
        fuentes = []
        
        for i, r in enumerate(results[:3], 1):
            context_parts.append(f"[Fuente {i}: {r['fuente']} - {r['tipo']}]\n{r['texto']}")
            fuentes.append({
                "fuente": r['fuente'],
                "tipo": r['tipo'],
                "similitud": r.get('similitud', 0),
                "texto": r['texto'][:200]
            })
        
        context = "\n\n---\n\n".join(context_parts)
        respuesta = self._call_ollama(query, context)
        
        return {
            "respuesta": respuesta,
            "fuentes": fuentes
        }


class REBT_CLI:
    def __init__(self):
        self.search = REBT_Search()
        print("✅ RAG REBT cargado")
    
    def run(self):
        print("\n🔍 Buscador REBT")
        print("-" * 30)
        print("Comandos:")
        print("  /normativa <búsqueda>  - Buscar en normativa")
        print("  /ejercicios <búsqueda>  - Buscar en ejercicios")
        print("  /salir             - Salir")
        
        while True:
            query = input("\n🔍 ").strip()
            if not query:
                continue
            
            if query.lower() in ["/salir", "salir"]:
                break
            
            if query.startswith("/normativa "):
                query = query[10:]
                results = self.search.buscar_normativa(query)
            elif query.startswith("/ejercicios "):
                query = query[11:]
                results = self.search.buscar_ejercicios(query)
            else:
                results = self.search.buscar(query)
            
            if results:
                for i, r in enumerate(results, 1):
                    print(f"\n{i}. [{r['fuente']}] ({r['tipo']})")
                    print(f"   {r['texto'][:200]}...")
            else:
                print("❌ Sin resultados")


if __name__ == "__main__":
    cli = REBT_CLI()
    cli.run()