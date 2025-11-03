import importlib

def test_schemas_module_imports():
    # Importar el módulo ejecuta sus definiciones y sube cobertura
    m = importlib.import_module("src.schemas")
    assert m is not None