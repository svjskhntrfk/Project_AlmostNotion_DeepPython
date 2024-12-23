document.addEventListener('DOMContentLoaded', function() {
    // ... существующий код ...

    // Добавляем обработчик для кнопки добавления изображения
    const addImgBtn = document.getElementById('addImg');
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = 'image/*';
    fileInput.style.display = 'none';
    document.body.appendChild(fileInput);

    addImgBtn.addEventListener('click', function() {
        fileInput.click();
    });

    fileInput.addEventListener('change', async function() {
        if (!this.files || !this.files[0]) return;

        const formData = new FormData();
        formData.append('file', this.files[0]);

        try {
            const boardId = window.location.pathname.split('/')[3];
            const response = await fetch(`/board/main_page/${boardId}/add_image`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) throw new Error('Failed to upload image');

            const data = await response.json();

            // Добавляем изображение в контейнер
            const imagesContainer = document.querySelector('.images');
            const newImage = document.createElement('img');
            newImage.src = data.image_url;
            newImage.alt = 'Image';
            imagesContainer.appendChild(newImage);

        } catch (error) {
            console.error('Error uploading image:', error);
            alert('Ошибка при загрузке изображения');
        }
    });

});
