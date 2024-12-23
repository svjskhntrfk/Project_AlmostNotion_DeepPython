async function uploadImage(event) {
    event.preventDefault();
    const file = event.target.files[0];

    if (!file) return;

    const currentMainSrc = document.getElementById('user_photo_main').src;
    const currentHeaderSrc = document.getElementById('user_photo_header').src;

    try {
        const reader = new FileReader();
        reader.onload = function(e) {
            const confirmButton = document.createElement('button');
            confirmButton.textContent = 'Сохранить фото';
            confirmButton.className = 'confirm-photo-btn';
            confirmButton.onclick = () => confirmUpload(file);

            const photoInfo = document.querySelector('.photo_info');

            const existingBtn = photoInfo.querySelector('.confirm-photo-btn');
            if (existingBtn) {
                existingBtn.remove();
            }
            photoInfo.appendChild(confirmButton);
        };

        reader.readAsDataURL(file);
    } catch (error) {
        console.error('Error:', error);
        displayError("An error occurred while processing the image.");
    }
}

async function confirmUpload(file, currentMainSrc, currentHeaderSrc) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/board/upload-image', {
            method: 'POST',
            body: formData,
            headers: {
                'Accept': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error('Upload failed');
        }

        const data = await response.json();
        if (data.url) {
            const finalUrl = data.url;

            const confirmButton = document.querySelector('.confirm-photo-btn');
            if (confirmButton) {
                confirmButton.remove();
            }

            setTimeout(() => {
                window.location.reload();
            }, 500);
        } else {
            throw new Error('No URL in response');
        }
    } catch (error) {
        console.error('Upload error:', error);
        displayError("Произошла ошибка при загрузке изображения. Maximum file size: 5MB");
    }
}

function displayError(message) {
    const errorMessageDiv = document.getElementById("error-message-upload");
    errorMessageDiv.textContent = message;
    errorMessageDiv.style.display = "block";
}