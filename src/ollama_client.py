"""
Cliente REBT RAG - Sin Ollama
Solo búsquedas en documentos normativa y ejercicios
"""

from typing import List, Dict
from src.rag_vectorstore import VectorStore


SYSTEM_PROMPT = """Eres un assistente REBT que busca información en documentos.
Respondes solo con la información encontrada en los documentos.
Si no hay información relevante, Indicas que no has encontrado资料."""


class REBT_Search:
    def __init__(self):
        from src.rag_vectorstore import VectorStore
        self.vectorstore = VectorStore()
    
    def buscar(self, query: str, n_resultados: int = 5) -> List[dict]:
        return self.vectorstore.buscar(query, n_resultados)
    
    def buscar_normativa(self, query: str, n_resultados: int = 5) -> List[dict]:
        return self.vectorstore.buscar_por_tipo(query, "normativa", n_resultados)
    
    def buscar_ejercicios(self, query: str, n_resultados: int = 5) -> List[dict]:
        return self.vectorstore.buscar_por_tipo(query, "ejercicios", n_resultados)
    
    def buscar_proyectos(self, query: str, n_resultados: int = 5) -> List[dict]:
        return self.vectorstore.buscar_por_tipo(query, "proyecto", n_resultados)
    
    def responder(self, query: str) -> str:
        results = self.buscar(query)
        
        if not results:
            return "No he encontrado información relevante."
        
        respuesta = f"📚 Resultados para: '{query}'\n\n"
        
        for i, r in enumerate(results, 1):
            similitud = r.get("similitud", 0) * 100
            respuesta += f"**{i}. [{r['fuente']}]** ({r['tipo']}) - Relevancia: {similitud:.0f}%\n\n"
            respuesta += f"{r['texto'][:400]}...\n\n"
            respuesta += "---\n\n"
        
        return respuesta


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