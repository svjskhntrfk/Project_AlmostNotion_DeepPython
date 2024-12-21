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

    addTodoBtn.addEventListener('click', async function() {
        const title = prompt("Введите название списка задач:");
        if (!title) return;

        todoInputContainer.style.display = 'block';
        todoInput.focus();
        todoInput.setAttribute('data-awaiting-first-task', 'true');
        todoInput.setAttribute('data-todo-list-title', title);
    });

    todoInput.addEventListener('keydown', async function(event) {
        if (event.key === 'Enter') {
            const text = this.value.trim();
            if (!text) {
                todoInputContainer.style.display = 'none';
                return;
            }

            const isFirstTask = this.getAttribute('data-awaiting-first-task') === 'true';

            try {
                if (isFirstTask) {
                    // Create new todo list with first task
                    const title = this.getAttribute('data-todo-list-title');
                    const response = await fetch(`/board/main_page/${boardId}/add_to_do_list`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            title: title,
                            text: text
                        })
                    });

                    if (!response.ok) throw new Error('Failed to create todo list');
                    
                    const data = await response.json();
                    currentTodoListId = data.to_do_list_id;
                    
                    // Create new todo list container
                    const todoListContainer = document.createElement('div');
                    todoListContainer.className = 'todo-list';
                    todoListContainer.setAttribute('data-todo-list-id', currentTodoListId);
                    
                    // Add title
                    const titleElement = document.createElement('h3');
                    titleElement.textContent = title;
                    todoListContainer.appendChild(titleElement);
                    
                    // Add first task
                    const taskElement = createTaskElement(text, data.to_do_list_new_item);
                    todoListContainer.appendChild(taskElement);
                    
                    todoList.appendChild(todoListContainer);
                    
                    this.removeAttribute('data-awaiting-first-task');
                    this.removeAttribute('data-todo-list-title');
                } else if (currentTodoListId) {
                    // Add new task to existing todo list
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
                }

                this.value = '';
            } catch (error) {
                console.error('Error:', error);
                alert('Произошла ошибка при сохранении задачи');
            }
        }
    });

    function createTaskElement(text, taskId) {
        const taskElement = document.createElement('div');
        taskElement.className = 'todo-task';
        taskElement.setAttribute('data-task-id', taskId);
        taskElement.setAttribute('data-completed', completed);
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.addEventListener('change', async function() {
            try {
                const todoListId = this.closest('.todo-list').getAttribute('data-todo-list-id');
                const taskId = this.closest('.todo-task').getAttribute('data-task-id');
                console.log('Updating task:', {
                    todoListId,
                    taskId,
                    completed: this.checked
                });
                
                await fetch(`/board/main_page/${boardId}/update_to_do_list_item`, {
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
            } catch (error) {
                console.error('Error updating task:', error);
                this.checked = !this.checked;
            }
        });

        const textSpan = document.createElement('span');
        textSpan.textContent = text;
        
        taskElement.appendChild(checkbox);
        taskElement.appendChild(textSpan);
        
        return taskElement;
    }

    // Add event listeners to existing checkboxes
    document.querySelectorAll('.todo-task input[type="checkbox"]').forEach(checkbox => {
        checkbox.addEventListener('change', async function() {
            try {
                const todoListId = this.closest('.todo-list').getAttribute('data-todo-list-id');
                const taskId = this.closest('.todo-task').getAttribute('data-task-id');
                console.log('Updating task:', {
                    todoListId,
                    taskId,
                    completed: this.checked
                });
                
                await fetch(`/board/main_page/${boardId}/update_to_do_list_item`, {
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
            } catch (error) {
                console.error('Error updating task:', error);
                this.checked = !this.checked;
            }
        });
    });
});