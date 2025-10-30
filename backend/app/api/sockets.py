import asyncio

from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    Query,
)
from app.logging.logger import log, ACTIVE_WEBSOCKETS


router = APIRouter(tags=['WebSockets'])


@router.websocket('/ws/logs')
async def open_log_websocket(
        websocket: WebSocket,
        timeout: int = Query(default=600, min=1),
    ) -> None:
    """
    Open a websocket for all live log messages.

    - timeout: The maximum number of seconds to keep the connection
    alive.
    """

    # Connect
    await websocket.accept()

    # Add to active set so log messages can be sent
    global ACTIVE_WEBSOCKETS
    for connection in list(ACTIVE_WEBSOCKETS):
        try:
            await connection.close()
        # Handle if WebSocket has already been closed
        except RuntimeError:
            pass
        finally:
            ACTIVE_WEBSOCKETS.discard(connection)
    ACTIVE_WEBSOCKETS.add(websocket)

    # Begin permanent connection
    start_time = asyncio.get_event_loop().time()
    try:
        while True:
            await log.complete()
            if asyncio.get_event_loop().time() - start_time > timeout:
                log.trace(f'Closed WebSocket after {timeout} seconds')
                break

            # Keep the Connection alive
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        ACTIVE_WEBSOCKETS.discard(websocket)
    finally:
        try:
            await websocket.close()
        except Exception:
            pass 
