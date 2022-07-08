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
    var applyFilterButton = django.jQuery("#ow-apply-filter"); 
    var filterElement = django.jQuery(target);
    var val = filterElement.val() || "";
    var class_name = filterElement.attr("class");
    var param = filterElement.attr("name");
    /* jshint -W117 */
    var filterQuery = search_replace(param, val);
    /* jshint +W117 */
    if (applyFilterButton.length === 0) {
      if (class_name.includes("admin-autocomplete")) {
        window.location.search = filterQuery;
      }
    } else {
      django.jQuery(target).append(
        `<div class="filter-options">
          <a class="selected" href="${filterQuery}"></a>
        </div>`
      );
    }
  }

  django.jQuery(".auto-filter").on("select2:select", function (event) {
    applyFilter(event.target);
  });

  django.jQuery(".auto-filter").on("select2:clear", function (event) {
    applyFilter(event.target);
  });
});
