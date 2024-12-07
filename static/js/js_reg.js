function validateForm(event) {
    let user_email = document.getElementById("email").value;
    let user_name = document.getElementById("username").value;
    let user_password = document.getElementById("password").value;
    let user_password2 = document.getElementById("password2").value;

    let user_email_Error = document.getElementById("email_Error");
    let user_name_Error = document.getElementById("name_Error");
    let user_password_Error = document.getElementById("password_Error");
    let user_password2_Error = document.getElementById("password2_Error");

    user_email_Error.textContent = "";
    user_name_Error.textContent = "";
    user_password_Error.textContent = "";
    user_password2_Error.textContent = "";

    let flag = true;

    const emailRegex = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/;
    
    if (!emailRegex.test(user_email)) {
        user_email_Error.textContent = "Пожалуйста, введите правильный E-mail (например: example@domain.com)";
        flag = false;
    }

    if (user_password !== user_password2) {
        user_password2_Error.textContent = "Пароли не совпадают.";
        flag = false;
    }

    if (user_password.length < 6) {
        user_password_Error.textContent = "Пароль должен содержать минимум 6 символов.";
        flag = false;
    }

    if (!flag) {
        event.preventDefault();
    }

    return flag;
}


const form = document.getElementById('regForm');
form.addEventListener('submit', function(event) {
    if (!validateForm(event)) {
        event.preventDefault();
    }
});
