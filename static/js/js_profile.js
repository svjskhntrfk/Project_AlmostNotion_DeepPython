async function uploadImage(event) {
    event.preventDefault();
    const file = event.target.files[0];

    if (!file) return;

    const currentMainSrc = document.getElementById('user_photo_main').src;
    const currentHeaderSrc = document.getElementById('user_photo_header').src;

    try {
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('user_photo_main').src = e.target.result;
            document.getElementById('user_photo_header').src = e.target.result;

            const confirmButton = document.createElement('button');
            confirmButton.textContent = 'Сохранить фото';
            confirmButton.className = 'confirm-photo-btn';
            confirmButton.onclick = () => confirmUpload(file, currentMainSrc, currentHeaderSrc);

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
        document.getElementById('user_photo_main').src = currentMainSrc;
        document.getElementById('user_photo_header').src = currentHeaderSrc;
        console.error('Upload error:', error);
        displayError("Произошла ошибка при загрузке изображения. Maximum file size: 5MB");
    }
}

function displayError(message) {
    const errorMessageDiv = document.getElementById("error-message-upload");
    errorMessageDiv.textContent = message;
    errorMessageDiv.style.display = "block";
}

document.getElementById("changePasswordForm").addEventListener("submit", async function(event) {
    event.preventDefault();  

    const oldPassword = document.getElementById("old_password").value;
    const newPassword = document.getElementById("new_password").value;

    document.getElementById("error-message-password").style.display = "none";

    const formData = new FormData();
    formData.append("old_password", oldPassword);
    formData.append("new_password", newPassword);

    try {
        const response = await fetch("/profile/main_page/profile/change_password", {
            method: "POST",
            body: formData
        });

        if (response.ok) {
            const data = await response.json();
            window.location.href = "/login";  
        } else {
            const errorData = await response.json();
            displayErrorPassword(errorData.detail || "Неизвестная ошибка. Попробуйте ещё раз.");
        }
    } catch (error) {
        console.error("Ошибка при изменении пароля:", error);
    }
});


function displayErrorPassword(message) {
    const errorMessageDiv = document.getElementById("error-message-password");
    errorMessageDiv.textContent = message;
    errorMessageDiv.style.display = "block";
}
