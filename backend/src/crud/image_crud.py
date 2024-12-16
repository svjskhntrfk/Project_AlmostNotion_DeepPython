from models import Image, ImageCreate, ImageUpdate

class ImageDAO[Image, ImageCreate, ImageUpdate]:

    async def _reset_is_main(self, model_name: str, model_instance: Base, association_table_name: str, db_session: AsyncSession):
        """Сбрасывает значение is_main для всех изображений, связанных с моделью."""
        association_table = Table(association_table_name, Base.metadata, autoload_with=db_session.bind)
        image_alias = aliased(Image)
        stmt = (
            select(image_alias.id)
            .select_from(association_table)
            .join(image_alias, association_table.c["image_id"] == image_alias.id)
            .where(association_table.c[f"{model_name}_id"] == model_instance.id)
            .where(image_alias.is_main == True)  # noqa: E712
        )
        result = await db_session.execute(stmt)
        image_ids = [row[0] for row in result.fetchall()]
        if image_ids:
            stmt = (
                update(Image)
                .where(Image.id.in_(image_ids))
                .values(is_main=False)
            )
            await db_session.execute(stmt)
            await db_session.commit()


    async def _get_image_url(self, db_obj: Image) -> ImageDAOResponse:
        """Получает URL к экземпляру Image."""
        url = await db_obj.storage.generate_url(db_obj.file)
        return ImageDAOResponse(image=db_obj, url=url)

    async def create_with_file(
            self, *, file: UploadFile, is_main: bool, model_instance: Type[Base], path: str = "",
            db_session: AsyncSession | None = None
    ) -> Image | None:
        model_name, association_table_name = await self._check_association_table(
            model_instance=model_instance,
            related_model=self.model,
            db_session=db_session
        )

        if is_main:
            await self._reset_is_main(model_name, model_instance, association_table_name, db_session)

        db_obj = self.model(is_main=is_main)
        db_obj.file = await db_obj.storage.put_object(file, path)
        db_session.add(db_obj)
        await db_session.flush()

        association_table = Table(association_table_name, Base.metadata, autoload_with=db_session.bind)
        stmt = association_table.insert().values(**{f"{model_name}_id": model_instance.id, "image_id": db_obj.id})
        await db_session.execute(stmt)
        await db_session.commit()
        await db_session.refresh(db_obj)

        return db_obj

image_dao = ImageDAO(Image)
