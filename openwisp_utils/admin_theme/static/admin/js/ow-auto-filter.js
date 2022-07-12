"use strict";
django.jQuery(document).ready(function () {
  // unbinding default event handlers of admin_auto_filters
  django.jQuery("#changelist-filter select, #grp-filters select").off("change");
  function setAllPlaceholder(target = null) {
    var allPlaceholder = gettext("All"),
      placeholderSelector = ".select2-selection__placeholder";
    if (target) {
      // using setTimeout to execute this after internal select2 events
      setTimeout(function () {
        django
          .jQuery(target)
          .parent()
          .find(placeholderSelector)
          .text(allPlaceholder);
      }, 100);
    } else {
      django.jQuery(`.auto-filter ${placeholderSelector}`).text(allPlaceholder);
    }
  }
  setAllPlaceholder();
  django.jQuery(".auto-filter").on("select2:open", function (event) {
    var optionsContainer = django
        .jQuery(event.target)
        .parent()
        .parent()
        .siblings()
        .last(),
      dropDownContainer = django
        .jQuery(optionsContainer)
        .find(".select2-container--open")[1];
    django.jQuery(optionsContainer).css("min-height", "14.75rem");
    django.jQuery(dropDownContainer).appendTo(optionsContainer);
    django.jQuery(dropDownContainer).removeAttr("style");
  });

  django.jQuery(".auto-filter").on("select2:close", function () {
    django.jQuery(".auto-filter-choices").css("min-height", "");
  });

  function applyFilter(target) {
    var applyFilterButton = django.jQuery("#ow-apply-filter"),
      filterElement = django.jQuery(target),
      val = filterElement.val() || "",
      param = filterElement.attr("name"),
      class_name = filterElement.attr("class");
    /* jshint -W117 */
    var filterQuery = search_replace(param, val);
    /* jshint +W117 */
    if (!applyFilterButton.length) {
      if (class_name.includes("admin-autocomplete")) {
        window.location.search = filterQuery;
      }
    } else {
      django.jQuery(target).find(".filter-options").remove();
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
    setAllPlaceholder(event.target);
    applyFilter(event.target);
  });
});
