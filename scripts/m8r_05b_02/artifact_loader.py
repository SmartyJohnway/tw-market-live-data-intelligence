import json
from pathlib import Path
from .models import AuthorizationError
def load_json(path):
 try: value=json.loads(Path(path).read_text(encoding='utf-8'))
 except (OSError,json.JSONDecodeError) as e: raise AuthorizationError('authorization_schema_invalid') from e
 if not isinstance(value,dict): raise AuthorizationError('authorization_schema_invalid')
 return value
