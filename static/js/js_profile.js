const fileInput = document.getElementById('file_input');
const userPhoto_main = document.getElementById('user_photo_main');
const userPhoto_header = document.getElementById('user_photo_header');

fileInput.addEventListener('change', function(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            userPhoto_main.src = e.target.result;
            userPhoto_header.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }
});
