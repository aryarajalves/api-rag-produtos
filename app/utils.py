import uuid

def ensure_uuid(req_id: str) -> str:
    """
    Garante que o ID seja um UUID válido.
    Se a string já for um UUID, retorna ela mesma.
    Se não for, gera um UUID v5 determinístico baseado nela.
    Isso permite usar números de telefone/IDs legíveis que sempre gerarão o mesmo UUID no banco.
    """
    try:
        # Tenta validar se já é UUID
        uuid_obj = uuid.UUID(req_id)
        return str(uuid_obj)
    except ValueError:
        # Se falhar, gera um UUID v5 usando um namespace fixo (DNS) e a string do ID
        # Isso garante que "zap_123" sempre gere o mesmo UUID.
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, req_id))

if __name__ == "__main__":
    # Teste rápido
    id1 = "123456"
    uuid1 = ensure_uuid(id1)
    print(f"'{id1}' -> {uuid1}")
    
    id2 = "123456" # Repetido para provar determinismo
    uuid2 = ensure_uuid(id2)
    print(f"'{id2}' -> {uuid2}")
    
    assert uuid1 == uuid2
    print("Teste OK!")
