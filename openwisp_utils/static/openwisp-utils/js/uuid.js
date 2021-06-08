'use strict';
django.jQuery(function ($) {
    var container = $('.field-uuid .readonly').eq(0),
        value = container.text();
    container.html('<input readonly id="id_id" type="text" class="vTextField readonly" value="' + value + '">');
    var id = $('#id_id');
    id.click(function () {
        $(this).select();
    });
});
