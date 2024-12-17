document.addEventListener('DOMContentLoaded', function() {
    const notesContainer = document.getElementById('notesContainer');
    const newNote = document.getElementById('newNote');
    const boardId = window.location.pathname.split('/')[3];

    if (!boardId) {
        console.error('Board ID not found in URL');
        return;
    }

    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    async function saveNoteChanges(textId, newText) {
        try {
            const response = await fetch(`/board/main_page/${boardId}/update_text`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text_id: textId,
                    text: newText.trim()
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to save note');
            }
        } catch (error) {
            console.error('Error saving note:', error);
        }
    }

    async function createNewNote(text) {
        try {
            const response = await fetch(`/board/main_page/${boardId}/add_text`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: text.trim() })
            });
            
            if (!response.ok) {
                throw new Error('Failed to create note');
            }
            
            const data = await response.json();
            return data.text_id;
        } catch (error) {
            console.error('Error creating note:', error);
        }
    }

    // Handle line breaks and preserve them
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            document.execCommand('insertLineBreak');
        }
    });

    // Handle existing notes editing with debounce
    const debouncedSave = debounce((textId, newText) => {
        saveNoteChanges(textId, newText);
    }, 500); // Reduced debounce time for better responsiveness

    notesContainer.addEventListener('input', (e) => {
        const noteContent = e.target.closest('.note-content');
        if (noteContent) {
            const textElement = noteContent.closest('.text');
            const textId = textElement.dataset.textId;
            debouncedSave(textId, noteContent.innerText);
        }
    });

    // Handle new note creation
    let isCreatingNote = false;
    newNote.addEventListener('input', debounce(async (e) => {
        if (isCreatingNote) return;
        
        const text = e.target.innerText.trim();
        if (text) {
            isCreatingNote = true;
            const textId = await createNewNote(text);
            if (textId) {
                const noteDiv = document.createElement('div');
                noteDiv.className = 'text';
                noteDiv.dataset.textId = textId;
                
                const noteContent = document.createElement('pre');
                noteContent.className = 'note-content';
                noteContent.contentEditable = true;
                noteContent.textContent = text;
                
                noteDiv.appendChild(noteContent);
                notesContainer.appendChild(noteDiv);
                
                e.target.innerText = '';
            }
            isCreatingNote = false;
        }
    }, 500));
}); 