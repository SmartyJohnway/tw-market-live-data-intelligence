class AuthorizationError(ValueError):
 def __init__(self,code,message=None): super().__init__(message or code); self.code=code
