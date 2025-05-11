function validateIPK(input) {
    const value = parseFloat(input.value);
    const error = document.getElementById('ipk-error');
    if (value < 3.0 || value > 4.0) {
        error.classList.remove('hidden');
        input.setCustomValidity('IPK harus antara 3.0 dan 4.0');
    } else {
        error.classList.add('hidden');
        input.setCustomValidity('');
    }
}

function formatPOT(input) {
    let value = input.value.replace(/[^0-9]/g, ''); // Remove non-numeric characters
    value = parseInt(value) || 0; // Convert to integer, default to 0 if invalid
    input.value = value.toLocaleString('id-ID'); // Format with commas
}

function validatePOT(input) {
    let value = input.value.replace(/[^0-9]/g, ''); // Remove commas for validation
    value = parseInt(value) || 0;
    const error = document.getElementById('pot-error');
    if (value < 0 || value > 7000000) {
        error.classList.remove('hidden');
        input.setCustomValidity('Penghasilan harus antara 0 dan 7.000.000');
    } else {
        error.classList.add('hidden');
        input.setCustomValidity('');
    }
    // Re-format after validation
    input.value = value.toLocaleString('id-ID');
}

function validateJTO(input) {
    const value = parseInt(input.value);
    const error = document.getElementById('jto-error');
    if (value < 1 || value > 5) {
        error.classList.remove('hidden');
        input.setCustomValidity('Tanggungan harus antara 1 dan 5');
    } else {
        error.classList.add('hidden');
        input.setCustomValidity('');
    }
}

function validateForm() {
    const ipk = document.getElementById('ipk');
    const pot = document.getElementById('pot');
    const jto = document.getElementById('jto');
    validateIPK(ipk);
    validatePOT(pot);
    validateJTO(jto);
    return ipk.checkValidity() && pot.checkValidity() && jto.checkValidity();
}