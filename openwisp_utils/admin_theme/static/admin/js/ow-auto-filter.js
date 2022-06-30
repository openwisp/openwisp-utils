"use strict";
django.jQuery(document).ready(function () {
  // unbinding default event handlers of admin_auto_filters
  django.jQuery("#changelist-filter select, #grp-filters select").off("change");

  django.jQuery(".auto-filter").on("select2:open", function (event) {
    var optionsContainer = django
        .jQuery(event.target)
        .parent()
        .parent()
        .siblings()
        .last(),
      dropDownContainer = django.jQuery(".select2-container--open")[1];
    django.jQuery(optionsContainer).css("min-height", "14.75rem");
    django.jQuery(dropDownContainer).appendTo(optionsContainer);
    django.jQuery(dropDownContainer).removeAttr("style");
  });

  django.jQuery(".auto-filter").on("select2:close", function () {
    django.jQuery(".auto-filter-choices").css("min-height", "");
  });

  function applyFilter(target) {
    var filterElement = django.jQuery(target);
    var val = filterElement.val() || "";
    var class_name = filterElement.attr("class");
    var param = filterElement.attr("name");
    if (class_name.includes("admin-autocomplete")) {
      /* jshint -W117 */
      window.location.search = search_replace(param, val);
      /* jshint +W117 */
    }
  }

  django.jQuery(".auto-filter").on("select2:select", function (event) {
    applyFilter(event.target);
  });

  django.jQuery(".auto-filter").on("select2:clear", function (event) {
    applyFilter(event.target);
  });
});
