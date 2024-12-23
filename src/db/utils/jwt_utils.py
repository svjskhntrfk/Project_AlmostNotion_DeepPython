from ..models import *
from ..database import *

async def create_jwt_tokens(
  tokens: list[dict], 
  user: User, 
  device_id: str, 
  session: AsyncSession
) -> None:
  print('in database')
  """
  Create multiple JWT tokens in database

  Args:
      tokens: List of token payloads containing 'jti' and 'exp'
      user: User instance
      device_id: Device identifier
      session: AsyncSession instance
  """
  issued_tokens = [
      IssuedJWTToken(
          subject=user,
          jti=token['jti'],
          device_id=device_id,
          expired_time=token['exp']
      )
      for token in tokens
  ]
  print(issued_tokens)
  print('end')
  session.add_all(issued_tokens)
  await session.commit()