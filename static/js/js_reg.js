async function checkEmailExists(email) {
    try {
        const response = await fetch(`/users/check_email/${email}`);
        const data = await response.json();
        return data.exists;
    } catch (error) {
        console.error('Error checking email:', error);
        return false;
    }
}

async function validateForm(event) {
    event.preventDefault(); // Предотвращаем отправку формы до проверки

    let user_email = document.getElementById("email").value;
    let user_name = document.getElementById("username").value;
    let user_password = document.getElementById("password").value;
    let user_password2 = document.getElementById("password2").value;

    let user_email_Error = document.getElementById("email_Error");
    let user_name_Error = document.getElementById("name_Error");
    let user_password_Error = document.getElementById("password_Error");
    let user_password2_Error = document.getElementById("password2_Error");

    // Очищаем предыдущие сообщения об ошибках
    user_email_Error.textContent = "";
    user_name_Error.textContent = "";
    user_password_Error.textContent = "";
    user_password2_Error.textContent = "";

    let flag = true;

    // Регулярное выражение для проверки email
    const emailRegex = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/;
    
    // Проверка email
    if (!emailRegex.test(user_email)) {
        user_email_Error.textContent = "Пожалуйста, введите правильный E-mail (например: example@domain.com)";
        user_email_Error.style.display = "block"; // Явно показываем сообщение об ошибке
        flag = false;
    } else {
        // Проверяем, существует ли уже такой email
        const emailExists = await checkEmailExists(user_email);
        if (emailExists) {
            user_email_Error.textContent = "Этот E-mail уже зарегистрирован";
            user_email_Error.style.display = "block"; // Явно показываем сообщение об ошибке
            flag = false;
        }
    }

    // Проверка длины пароля
    if (user_password.length < 6) {
        user_password_Error.textContent = "Пароль должен содержать минимум 6 символов";
        user_password_Error.style.display = "block"; // Явно показываем сообщение об ошибке
        flag = false;
    }

    // Проверка совпадения паролей
    if (user_password !== user_password2) {
        user_password2_Error.textContent = "Пароли не совпадают";
        user_password2_Error.style.display = "block"; // Явно показываем сообщение об ошибке
        flag = false;
    }

    if (flag) {
        document.getElementById('regForm').submit(); // Отправляем форму если все проверки пройдены
    }
}

// Добавляем обработчик события submit для формы
const form = document.getElementById('regForm');
form.addEventListener('submit', validateForm);
