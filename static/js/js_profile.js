async function uploadImage(event) {
    event.preventDefault();
    const file = event.target.files[0];

    if (!file) return;

    // Keep track of current images in case we need to revert
    const currentMainSrc = document.getElementById('user_photo_main').src;
    const currentHeaderSrc = document.getElementById('user_photo_header').src;

    try {
        // Show preview and confirmation button
        const reader = new FileReader();
        reader.onload = function(e) {
            // Set preview
            document.getElementById('user_photo_main').src = e.target.result;
            document.getElementById('user_photo_header').src = e.target.result;

            // Show confirmation button
            const confirmButton = document.createElement('button');
            confirmButton.textContent = 'Сохранить фото';
            confirmButton.className = 'confirm-photo-btn';
            confirmButton.onclick = () => confirmUpload(file, currentMainSrc, currentHeaderSrc);

            // Find the photo_info div and append the button
            const photoInfo = document.querySelector('.photo_info');
            // Remove existing button if any
            const existingBtn = photoInfo.querySelector('.confirm-photo-btn');
            if (existingBtn) {
                existingBtn.remove();
            }
            photoInfo.appendChild(confirmButton);
        };

        reader.readAsDataURL(file);
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while processing the image.');
    }
}

async function confirmUpload(file, currentMainSrc, currentHeaderSrc) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('is_main', 'true');

    try {
        const response = await fetch('/image/upload-image', {
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
            document.getElementById('user_photo_main').src = finalUrl;
            document.getElementById('user_photo_header').src = finalUrl;

            // Remove confirmation button after successful upload
            const confirmButton = document.querySelector('.confirm-photo-btn');
            if (confirmButton) {
                confirmButton.remove();
            }

            // Refresh the page after a short delay to ensure the upload is complete
            setTimeout(() => {
                window.location.reload();
            }, 500);
        } else {
            throw new Error('No URL in response');
        }
    } catch (error) {
        // Revert to previous images if upload fails
        document.getElementById('user_photo_main').src = currentMainSrc;
        document.getElementById('user_photo_header').src = currentHeaderSrc;
        console.error('Upload error:', error);
        displayError("Произошла ошибка при загрузке изображения. Maximum file size: 5MB");
    }
}

function displayError(message) {
    const errorMessageDiv = document.getElementById("error-message");
    errorMessageDiv.textContent = message;
    errorMessageDiv.style.display = "block";
}
