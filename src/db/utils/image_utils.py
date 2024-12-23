from ..models import *
from ..database import *

async def save_user_image(user_id: int, file: UploadFile, session: AsyncSession) -> Image:
    print(f"Starting save_user_image for user_id: {user_id}")
    try:
        # Получаем пользователя
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        print(f"Calling image_dao.create_with_file with path: Users")
        image = await image_dao.create_with_file(
            file=file,
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



async def delete_image(image_id: UUID, session: AsyncSession) -> None:
    """
    Удаляет изображение по его ID, удаляет файл из хранилища и удаляет все связи с пользователями.

    Args:
        image_id (UUID): ID изображения, которое нужно удалить.
        session (AsyncSession): Асинхронная сессия SQLAlchemy.

    Raises:
        HTTPException: Если изображение не найдено.
        RuntimeError: Если произошла ошибка при удалении изображения.
    """
    print(f"Starting delete_image for image_id: {image_id}")
    logger.info(f"Starting delete_image for image_id: {image_id}")
    try:
        image = await session.get(Image, image_id)
        if not image:
            logger.error(f"Image with id {image_id} not found.")
            raise HTTPException(status_code=404, detail="Image not found")

        if image.file:
            try:
                print(f"Deleting file from storage: {image.file}")
                logger.info(f"Deleting file from storage: {image.file}")
                await image.storage.delete_object(image.file)
            except Exception as file_error:
                logger.error(f"Failed to delete file {image.file} from storage: {file_error}")
                raise RuntimeError(f"Failed to delete file from storage: {file_error}") from file_error

        try:
            stmt = user_image_association.delete().where(user_image_association.c.image_id == image_id)
            await session.execute(stmt)
            logger.info(f"Deleted associations for image_id: {image_id}")
        except Exception as assoc_error:
            logger.error(f"Failed to delete associations for image_id {image_id}: {assoc_error}")
            raise RuntimeError(f"Failed to delete associations: {assoc_error}") from assoc_error

        try:
            await session.delete(image)
            await session.commit()
            logger.info(f"Successfully deleted image with ID: {image_id}")
            print(f"Successfully deleted image with ID: {image_id}")
        except Exception as db_error:
            await session.rollback()
            logger.error(f"Failed to delete image with id {image_id}: {db_error}")
            print(f"Failed to delete image with id {image_id}: {db_error}")
            raise RuntimeError(f"Failed to delete image: {db_error}") from db_error

    except HTTPException as e:
        logger.error(f"HTTPException in delete_image: {e.detail}")
        print(f"HTTPException in delete_image: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in delete_image: {str(e)}")
        print(f"Error in delete_image: {str(e)}")
        traceback_str = traceback.format_exc()
        logger.error(f"Traceback: {traceback_str}")
        print(f"Traceback: {traceback_str}")
        raise RuntimeError("An unexpected error occurred while deleting the image.") from e