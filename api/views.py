from rest_framework.decorators import api_view
from rest_framework.response import Response
from pydantic import ValidationError
from api.dto import CommandDTO, NoPwdCommandDTO, ScriptDTO
from server.utils.errors import ServerError
from server.service.dispatcher import dispatch_command

@api_view(["POST"])
def command(request):
    try:
        dto = CommandDTO(**request.data)
        result = dispatch_command("linux", dto.model_dump())
        return Response(result)
    except ValidationError as ve:
        return Response({"error": ve.errors()}, status=400)
    except ServerError as e:
        return Response({"error": str(e)}, status=400)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(["POST"])
def nopwd_command(request):
    try:
        dto = NoPwdCommandDTO(**request.data)
        result = dispatch_command("linux_nopwd", dto.model_dump())
        return Response(result)
    except ValidationError as ve:
        return Response({"error": ve.errors()}, status=400)
    except ServerError as e:
        return Response({"error": str(e)}, status=400)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(["POST"])
def script(request):
    try:
        dto = ScriptDTO(**request.data)
        result = dispatch_command("linux_script", dto.model_dump())
        return Response(result)
    except ValidationError as ve:
        return Response({"error": ve.errors()}, status=400)
    except ServerError as e:
        return Response({"error": str(e)}, status=400)
    except Exception as e:
        return Response({"error": str(e)}, status=500)
