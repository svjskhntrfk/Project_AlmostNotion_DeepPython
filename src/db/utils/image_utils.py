from ..models import *
from ..database import *

async def save_user_image(user_id: int, file: UploadFile, is_main: bool, session: AsyncSession) -> Image:
    print(f"Starting save_user_image for user_id: {user_id}")
    try:
        # Получаем пользователя
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        print(f"Calling image_dao.create_with_file with path: Users")
        image = await image_dao.create_with_file(
            file=file,
            is_main=is_main,
            model_instance=user,  # Передаем объект пользователя
            path="Users",
            db_session=session
        )
        await session.commit()
        return image
    except Exception as e:
        print(f"Error in save_user_image: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise

async def get_images_by_user_id(user_id: int, session: AsyncSession) -> List[Image]:
    print(f"Starting get_images_by_user_id for user_id: {user_id}")
    try:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        query = (
            select(Image)
            .outerjoin(user_image_association, Image.id == user_image_association.c.image_id)
            .where(or_(Image.user_id == user_id, user_image_association.c.user_id == user_id))
            .options(selectinload(Image.user))  # Опционально: загрузка связанных пользователей
        )

        result = await session.execute(query)
        images = result.scalars().all()

        print(f"Retrieved {len(images)} images for user_id: {user_id}")
        logger.info(f"Retrieved {len(images)} images for user_id: {user_id}")

        return [ImageSchema.from_orm(image) for image in images]

    except HTTPException as e:
        print(f"HTTPException in get_images_by_user_id: {e.detail}")
        logger.error(f"HTTPException in get_images_by_user_id: {e.detail}")
        raise e
    except Exception as e:
        print(f"Error in get_images_by_user_id: {str(e)}")
        print(f"Error type: {type(e)}")
        logger.error(f"Error in get_images_by_user_id: {str(e)}")
        traceback_str = traceback.format_exc()
        print(f"Traceback: {traceback_str}")
        logger.error(f"Traceback: {traceback_str}")
        raise RuntimeError("An unexpected error occurred while retrieving images.") from e

async def get_image_url(image_id: str, session: AsyncSession) -> str:
    image = await image_dao.get(id=image_id, db_session=session)
    return image.url
