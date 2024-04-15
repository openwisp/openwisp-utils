'use strict';

django.jQuery(document).ready(function($) {
    $('#id_user_consented').change(function() {
        $('#id_metric_collection_consent_form').submit();
    });
});
