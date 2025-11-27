from fastapi import Request
import httpx

async def get_http_client(request: Request) -> httpx.AsyncClient:
    """
    Devuelve el cliente HTTP compartido que se creó en el evento startup de main.py.
    Esto es mucho más eficiente que crear un cliente nuevo por cada petición.
    """
    return request.app.state.http_client