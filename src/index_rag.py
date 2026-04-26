#!/usr/bin/env python3
"""
Script de indexación RAG para REBT
Ejecutar: python src/index_rag.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag_vectorstore import VectorStore


def main():
    print("📚 Indexador RAG - REBT")
    print("=" * 50)
    
    store = VectorStore()
    
    print("\n1. Indexar todo")
    print("2. Indexar normativa")
    print("3. Indexar ejercicios")
    print("4. Buscar")
    print("5. Limpiar y reindexar")
    
    opcion = input("\nOpción [1]: ").strip() or "1"
    
    if opcion == "1":
        store.limpiar()
        store.indexar_todos()
    
    elif opcion == "2":
        from src.rag_extractor import NORMATIVA_DIR, listar_pdfs
        for pdf in listar_pdfs(NORMATIVA_DIR):
            try:
                store.indexar_documento(str(pdf), "normativa")
            except Exception as e:
                print(f"  ❌ Error: {e}")
    
    elif opcion == "3":
        from src.rag_extractor import EJERCICIOS_DIR, listar_pdfs
        for pdf in listar_pdfs(EJERCICIOS_DIR):
            try:
                store.indexar_documento(str(pdf), "ejercicios")
            except Exception as e:
                print(f"  ❌ Error: {e}")
    
    elif opcion == "4":
        query = input("Búsqueda: ").strip()
        if query:
            results = store.buscar(query)
            for i, r in enumerate(results, 1):
                print(f"\n{i}. [{r['fuente']}] ({r['tipo']}) - Similitud: {r.get('similitud', 0):.2f}")
                print(f"   {r['texto'][:150]}...")
    
    elif opcion == "5":
        confirm = input("¿Confirmar? (s/n): ").strip().lower()
        if confirm == "s":
            store.limpiar()
            store.indexar_todos()
    
    else:
        print("Opción no válida")


if __name__ == "__main__":
    main()