document.getElementById('addTodoBtn').addEventListener('click', function() {
    document.getElementById('todoInputContainer').style.display = 'block';
    document.getElementById('todoInput').focus();
});

document.getElementById('todoInput').addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        const inputValue = this.value.trim();
        if (inputValue) {
            const todoList = document.getElementById('todoList');
            const todoItem = document.createElement('div');
            todoItem.innerHTML = `<input type="checkbox"> ${inputValue}`;
            todoList.appendChild(todoItem);
            this.value = '';
        } else if (this.value === '') {
            document.getElementById('todoInputContainer').style.display = 'none';
        }
    }
});
