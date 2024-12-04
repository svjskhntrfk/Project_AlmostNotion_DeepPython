function validateForm() {
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

    if (!validator.isEmail(user_email)) {
        user_email_Error.textContent = "Please enter a valid email address";
        flag = false;
    }

    if (user_password !== user_password2) {
        user_password_Error.textContent = "Passwords do not match";
        flag = false;
    }

    return flag;
}
