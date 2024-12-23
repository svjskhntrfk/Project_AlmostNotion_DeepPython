document.getElementById('file_input').addEventListener('change', function(event) {
    // Show the submit button when a file is selected
    document.getElementById('submitImage').style.display = 'inline-block';

    // Optional: Show selected file name
    const fileName = event.target.files[0]?.name;
    if (fileName) {
        console.log('Selected file:', fileName);
    }
});

document.getElementById('uploadForm').addEventListener('submit', async function(event) {
    event.preventDefault();
    const boardId = window.location.pathname.split('/')[3];

    const formData = new FormData(this);
    try {
        const response = await fetch(`/board/main_page/${boardId}/add_image`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Upload failed');

        // Handle successful upload
        const result = await response.json();
        console.log('Upload successful:', result);

        // Reset form and hide submit button
        this.reset();
        document.getElementById('submitImage').style.display = 'none';

        setTimeout(() => {
           window.location.reload();
        }, 100);

    } catch (error) {
        console.error('Upload error:', error);
        alert('Ошибка при загрузке файла');
    }
});
