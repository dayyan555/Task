from fastapi.responses import JSONResponse


def create_json_response(success: bool, message: str, data: dict = None, status_code: int = 200):
    return JSONResponse(
        status_code=status_code,
        content={
            "success": success,
            "message": message,
            "data": data or {}
        }
    )