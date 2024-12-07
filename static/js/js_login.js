function validateLoginForm(event) {
    let user_email = document.getElementById("email").value;
    let user_password = document.getElementById("password").value;

    let user_email_Error = document.getElementById("email_Error");
    let user_password_Error = document.getElementById("password_Error");

    // Очищаем предыдущие сообщения об ошибках
    user_email_Error.textContent = "";
    user_password_Error.textContent = "";

    let flag = true;

    // Регулярное выражение для проверки email
    const emailRegex = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/;
    
    // Проверка email
    if (!emailRegex.test(user_email)) {
        user_email_Error.textContent = "Пожалуйста, введите правильный E-mail (например: example@domain.com)";
        flag = false;
    }

    // Проверка наличия пароля
    if (user_password.length < 1) {
        user_password_Error.textContent = "Введите пароль";
        flag = false;
    }

    if (!flag) {
        event.preventDefault();
    }

    return flag;
}

// Добавляем обработчик события submit для формы
const loginForm = document.getElementById('loginForm');
loginForm.addEventListener('submit', function(event) {
    if (!validateLoginForm(event)) {
        event.preventDefault();
    }
}); 