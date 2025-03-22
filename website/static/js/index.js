/* index.js */
$.ajaxSetup({
    beforeSend: function(xhr) {
        xhr.setRequestHeader("X-CSRFToken", "{{ csrf_token() }}");
    }
});