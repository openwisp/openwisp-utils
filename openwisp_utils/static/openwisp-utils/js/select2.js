"use strict";

django.jQuery(function ($) {
  function initSelect2($element) {
    $element.not('select[name*="__prefix__"]').each(function () {
      var $el = $(this);
      if (!$el.hasClass("select2-hidden-accessible")) {
        $el.select2();
      }
    });
  }

  initSelect2($("select.ow-select2"));

  $(document).on("formset:added", function (event, $row) {
    initSelect2($row.find("select.ow-select2"));
  });
});
