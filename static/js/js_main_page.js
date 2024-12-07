const openModalBtn = document.getElementById('openModalBtn');
const modal = document.getElementById('modal');
const confirmBtn = document.getElementById('confirmBtn');
const boardNameInput = document.getElementById('boardName');

openModalBtn.addEventListener('click', () => {
  modal.style.display = 'flex';
});

confirmBtn.addEventListener('click', () => {
  const boardName = boardNameInput.value.trim();
  if (boardName) {
    alert(`Доска "${boardName}" успешно добавлена!`);
    modal.style.display = 'none';
    boardNameInput.value = '';
  } else {
    alert('Пожалуйста, введите название доски.');
  }
});

window.addEventListener('click', (e) => {
  if (e.target === modal) {
    modal.style.display = 'none';
  }
});
