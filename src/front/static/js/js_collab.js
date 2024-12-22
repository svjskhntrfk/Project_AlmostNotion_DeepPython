const openModalBtn = document.getElementById('openModalBtn');
const modal = document.getElementById('modal');
const confirmBtn = document.getElementById('confirmBtn');
const boardNameInput = document.getElementById('email_collaborator');

openModalBtn.addEventListener('click', () => {
  modal.style.display = 'flex';
});

confirmBtn.addEventListener('click', () => {
  const boardName = boardNameInput.value.trim();
  if (boardName) {
    modal.style.display = 'none';
    boardNameInput.value = '';
  } else {
    alert('Пожалуйста, введите email коллаборатора.');
  }
});

window.addEventListener('click', (e) => {
  if (e.target === modal) {
    modal.style.display = 'none';
  }
});

function closeModal() {
    document.getElementById('modal').style.display = 'none';
}
