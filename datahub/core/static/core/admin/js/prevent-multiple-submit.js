/**
 * Prevent multiple form submissions by disabling the submit button once it's been
 * clicked.
 *
 * Currently only compatible with <input> (and not <button>).
 *
 * Example usage:
 *
 * With default loading text:
 *
 *   <input type="submit" value="Submit" data-prevent-multiple-submit>
 *
 * With custom loading text:
 *
 *   <input type="submit" value="Submit" data-prevent-multiple-submit="Submitting...">
 */

window.addEventListener('DOMContentLoaded', function () {
  var buttons = window.document.querySelectorAll('input[data-prevent-multiple-submit]');

  Array.prototype.forEach.call(buttons, function (button) {
    button.addEventListener('click', function (event) {
      event.preventDefault();

      if (!event.target.form.reportValidity || event.target.form.reportValidity()) {
        // event.target.getAttribute() used rather than event.target.dataset for IE<11 support
        event.target.value = event.target.getAttribute('data-prevent-multiple-submit') || 'Please wait...';
        event.target.disabled = true;
        event.target.form.submit();
      }
    })
  })
});
