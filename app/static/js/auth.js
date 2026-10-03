// Login and signup forms: check each field while it is filled in, with our own messages instead
// of the browser's bubbles, and let the password be shown in clear

function fieldError(input) {
    if (input.validity.valueMissing) return 'Required';
    if (input.validity.typeMismatch) return 'Not a valid email address';
    if (input.validity.tooShort) return `Must be at least ${input.minLength} characters long`;
    if (input.validity.patternMismatch) return 'Only letters, digits, dots, dashes and underscores';
    return '';
}

const form = document.querySelector('form.auth');
const inputs = [...form.querySelectorAll('.field input')];
const touched = new Set();
form.noValidate = true;

function check(input) {
    // Until a field has been left once, only clear its error (the server's included), so as not
    // to complain about a word still being typed
    const error = input.closest('.field').querySelector('.field-error');
    error.textContent = touched.has(input) ? fieldError(input) : '';
}

for (const input of inputs) {
    input.addEventListener('input', () => check(input));
    input.addEventListener('blur', () => {
        if (input.value) {
            touched.add(input);
            check(input);
        }
    });
}

form.addEventListener('submit', event => {
    inputs.forEach(input => {
        touched.add(input);
        check(input);
    });
    const invalid = inputs.find(input => !input.validity.valid);
    if (invalid) {
        event.preventDefault();
        invalid.focus();
    } else {
        // Send the password hidden again, for password managers to offer saving it
        form.querySelectorAll('.password input').forEach(input => input.type = 'password');
    }
});

for (const button of form.querySelectorAll('.reveal')) {
    const input = button.parentElement.querySelector('input');
    // Keep the focus (and the keyboard) on the field
    button.addEventListener('mousedown', event => event.preventDefault());
    button.addEventListener('click', () => {
        const shown = input.type === 'text';
        input.type = shown ? 'password' : 'text';
        button.textContent = shown ? 'Show' : 'Hide';
    });
}
