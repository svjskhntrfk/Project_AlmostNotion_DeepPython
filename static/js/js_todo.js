document.getElementById('addTodoBtn').addEventListener('click', function() {
    document.getElementById('todoInputContainer').style.display = 'block';
    document.getElementById('todoInput').focus();
});

document.addEventListener('DOMContentLoaded', function() {
    const todoList = document.getElementById('todoList');
    const todoInputContainer = document.getElementById('todoInputContainer');
    const todoInput = document.getElementById('todoInput');
    const addTodoBtn = document.getElementById('addTodoBtn');
    const boardId = window.location.pathname.split('/')[3];

    let currentTodoListId = null;

    // Add todo list button click handler
    addTodoBtn.addEventListener('click', async function() {
        const title = prompt("Введите название списка задач:");
        if (!title) return;

        try {
            const response = await fetch(`/board/main_page/${boardId}/add_to_do_list`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    title: title,
                    text: "Новая задача"  // Default first task
                })
            });

            if (!response.ok) throw new Error('Failed to create todo list');
            
            const data = await response.json();
            currentTodoListId = data.to_do_list_id;
            
            // Create and append new todo list
            const todoListElement = document.createElement('div');
            todoListElement.className = 'todo-list';
            todoListElement.setAttribute('data-todo-list-id', currentTodoListId);
            
            const titleElement = document.createElement('h3');
            titleElement.textContent = title;
            todoListElement.appendChild(titleElement);
            
            const taskElement = createTaskElement("Новая задача", data.to_do_list_new_item);
            todoListElement.appendChild(taskElement);
            
            todoList.appendChild(todoListElement);
            
            // Show input for additional tasks
            todoInputContainer.style.display = 'block';
            todoInput.focus();

        } catch (error) {
            console.error('Error:', error);
            alert('Произошла ошибка при создании списка');
        }
    });

    // Input for new tasks
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
                const taskElement = createTaskElement(text, data.to_do_list_new_item);
                currentList.appendChild(taskElement);
                
                this.value = '';
            } catch (error) {
                console.error('Error:', error);
                alert('Произошла ошибка при добавлении задачи');
            }
        }
    });

    // Create task element helper function
    function createTaskElement(text, taskId) {
        const taskElement = document.createElement('div');
        taskElement.className = 'todo-task';
        taskElement.setAttribute('data-task-id', taskId);
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
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
                this.checked = !this.checked;
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
});