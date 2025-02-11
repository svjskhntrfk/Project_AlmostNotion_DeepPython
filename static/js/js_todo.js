document.addEventListener('DOMContentLoaded', function() {
    const todoList = document.getElementById('todoList');
    const todoInputContainer = document.getElementById('todoInputContainer');
    const todoInput = document.getElementById('todoInput');
    const addTodoBtn = document.getElementById('addTodoBtn');
    const boardId = window.location.pathname.split('/')[3];

    let currentTodoListId = null;

    const modal = document.getElementById('modal_todo');
    const todoTitleInput = document.getElementById('todo-title-input');
    const cancelBtn = document.getElementById('cancel-btn');
    const submitBtn = document.getElementById('submit-btn');

    // Открытие модального окна
    addTodoBtn.addEventListener('click', function() {
        modal.style.display = 'flex'; // Показываем модальное окно
        todoTitleInput.focus(); // Фокус на поле ввода
    });

    // Закрытие модального окна при нажатии "Отмена"
    cancelBtn.addEventListener('click', function() {
        modal.style.display = 'none'; // Скрыть модал��ное окно
    });

    // Add todo list button click handler
    submitBtn.addEventListener('click', async function() {
        const title = todoTitleInput.value.trim();
        if (!title) return; // Если поле ввода пустое, не выполняем действие

        try {
            const response = await fetch(`/board/main_page/${boardId}/add_to_do_list`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    title: title,
                    text: "Новая задача, нажмите, чтобы изменить"  
                })
            });

            if (!response.ok) throw new Error('Failed to create todo list');

            const data = await response.json();
            currentTodoListId = data.to_do_list_id;

            const todoListElement = document.createElement('div');
            todoListElement.className = 'todo-list';
            todoListElement.setAttribute('data-todo-list-id', currentTodoListId);

            const titleElement = document.createElement('h3');
            titleElement.textContent = title;
            todoListElement.appendChild(titleElement);

            const taskElement = createTaskElement("Новая задача", data.to_do_list_new_item, false);  // Состояние false для нового чекбокса
            todoListElement.appendChild(taskElement);

            todoList.appendChild(todoListElement);

            modal.style.display = 'none';

            todoInputContainer.style.display = 'block';
            todoInput.focus();

        } catch (error) {
            console.error('Error:', error);
            alert('Произошла ошибка при создании списка');
        }
    });

    todoInput.addEventListener('keydown', async function(event) {
        if (event.key === 'Enter') {
            const text = this.value.trim();
            if (!text) return;

            try {
                const response = await fetch(`/board/main_page/${boardId}/add_to_do_list_item`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        to_do_list_id: currentTodoListId,
                        text: text
                    })
                });

                if (!response.ok) throw new Error('Failed to add task');

                const data = await response.json();
                const currentList = document.querySelector(`.todo-list[data-todo-list-id="${currentTodoListId}"]`);
                const taskElement = createTaskElement(text, data.to_do_list_new_item, false);  // Новая задача с состоянием unchecked
                currentList.appendChild(taskElement);

                this.value = '';
            } catch (error) {
                console.error('Error:', error);
                alert('Произошла ошибка при добавлении задачи');
            }
        }
    });

    function createTaskElement(text, taskId, isChecked) {
        const taskElement = document.createElement('div');
        taskElement.className = 'todo-task';
        taskElement.setAttribute('data-task-id', taskId);

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = isChecked; // Устанавливаем состояние чекбокса при создании задачи

        checkbox.addEventListener('change', async function() {
            const todoListId = this.closest('.todo-list').getAttribute('data-todo-list-id');
            try {
                const response = await fetch(`/board/main_page/${boardId}/update_to_do_list_item`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        to_do_list_id: todoListId,
                        to_do_list_item_id: taskId,
                        text: text,
                        completed: this.checked
                    })
                });

                if (!response.ok) {
                    throw new Error('Failed to update task');
                }
            } catch (error) {
                console.error('Error updating task:', error);
                this.checked = !this.checked;  // В случае ошибки восстанавливаем состояние
            }
        });

        const textSpan = document.createElement('span');
        textSpan.textContent = text;
        textSpan.contentEditable = true;
        textSpan.addEventListener('blur', async function() {
            const todoListId = this.closest('.todo-list').getAttribute('data-todo-list-id');
            const newText = this.textContent.trim();
            try {
                await fetch(`/board/main_page/${boardId}/update_to_do_list_item`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        to_do_list_id: todoListId,
                        to_do_list_item_id: taskId,
                        text: newText,
                        completed: checkbox.checked
                    })
                });
            } catch (error) {
                console.error('Error updating task text:', error);
                this.textContent = text;
            }
        });

        taskElement.appendChild(checkbox);
        taskElement.appendChild(textSpan);

        return taskElement;
    }

    // Добавляем инициализацию существующих задач
    const existingTasks = document.querySelectorAll('.todo-task');
    existingTasks.forEach(taskElement => {
        const checkbox = taskElement.querySelector('input[type="checkbox"]');
        const textSpan = taskElement.querySelector('span');
        const taskId = taskElement.getAttribute('data-task-id');
        const todoListId = taskElement.closest('.todo-list').getAttribute('data-todo-list-id');

        // Добавляем обработчик для checkbox
        checkbox.addEventListener('change', async function() {
            try {
                const response = await fetch(`/board/main_page/${boardId}/update_to_do_list_item`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        to_do_list_id: todoListId,
                        to_do_list_item_id: taskId,
                        text: textSpan.textContent,
                        completed: this.checked
                    })
                });

                if (!response.ok) {
                    throw new Error('Failed to update task');
                }
            } catch (error) {
                console.error('Error updating task:', error);
                this.checked = !this.checked;
            }
        });

        // Добавляем возможность редактирования
        textSpan.contentEditable = true;
        textSpan.addEventListener('blur', async function() {
            const newText = this.textContent.trim();
            try {
                const response = await fetch(`/board/main_page/${boardId}/update_to_do_list_item`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        to_do_list_id: todoListId,
                        to_do_list_item_id: taskId,
                        text: newText,
                        completed: checkbox.checked
                    })
                });

                if (!response.ok) {
                    throw new Error('Failed to update task');
                }
            } catch (error) {
                console.error('Error updating task text:', error);
            }
        });
    });
});

function submitDeadline() {
    const deadline = document.getElementById('deadline').value;
    // Здесь можно отправить данные на сервер или выполнить другие действия
}
