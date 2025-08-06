let lastClickTime = 0;

function throttleSubmit(form) {
    const now = Date.now();
    if (now - lastClickTime < 1000) {
        return false;
    }
    lastClickTime = now;

    const button = form.querySelector('#gaechoo_button');
    button.disabled = true;

    setTimeout(() => {
        button.disabled = false;
    }, 1000);

    return true;
}