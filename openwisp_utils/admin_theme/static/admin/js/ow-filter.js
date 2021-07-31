'use strict';
var leftArrow, rightArrow, slider;
const scrollDX = 200,
  btnAnimationTime = 100; //ms

(function () {
  document.addEventListener(
    'DOMContentLoaded',
    function () {
      leftArrow = document.querySelector('.filters-bottom .left-arrow');
      rightArrow = document.querySelector('.filters-bottom .right-arrow');
      slider = document.querySelector('.ow-filter-slider');
      initFilterDropdownHandler();
      initSliderHandlers();
      filterHandlers();
      setArrowButtonVisibility();
    },
    false
  );
})();

function initFilterDropdownHandler() {
  const filters = document.querySelectorAll('.ow-filter');
  // When filter title is clicked
  filters.forEach(function (filter) {
    var toggler = filter.querySelector('.filter-title');
    toggler.addEventListener('click', function () {
      // Close if any active filter
      var activeFilter = document.querySelector('.ow-filter.active');
      if (activeFilter) {
        activeFilter.classList.remove('active');
      }
      filter.classList.toggle('active');
    });
  });
  // Handle click outside of an active filter
  document.addEventListener('click', function (e) {
    var activeFilter = document.querySelector('.ow-filter.active');
    if (activeFilter && !activeFilter.contains(e.target)) {
      activeFilter.classList.remove('active');
    }
  });
  // Handle change in filter option
  const filterRadios = document.querySelectorAll('.filter-options input');
  filterRadios.forEach(function (filterRadio) {
    filterRadio.addEventListener('change', function () {
      let filter = document.querySelector('.ow-filter.active');
      let view = document.querySelector('.ow-filter.active .selected-option');
      let selectedElement = document.querySelector(
        '.ow-filter.active .selected'
      );
      selectedElement.classList.remove('selected');
      filterRadio.previousElementSibling.classList.add('selected');
      view.innerHTML = filterRadio.previousElementSibling.innerHTML;
      filter.classList.remove('active');
    });
  });
}

function ButtonAnimation(button) {
  // Animate button by adding and removing classes
  button.classList.add('down');
  setTimeout(function () {
    button.classList.remove('down');
  }, btnAnimationTime);
}

function scrollLeft() {
  ButtonAnimation(leftArrow);
  slider.scrollLeft -= scrollDX;
  if (slider.scrollLeft == 0) {
    leftArrow.classList.add('force-inactive');
  } else {
    leftArrow.classList.remove('force-inactive');
  }
  rightArrow.classList.remove('force-inactive');
}

function scrollRight() {
  ButtonAnimation(rightArrow);
  slider.scrollLeft += scrollDX;
  if (slider.scrollLeft + slider.offsetWidth >= slider.scrollWidth) {
    rightArrow.classList.add('force-inactive');
  } else {
    rightArrow.classList.remove('force-inactive');
  }
  leftArrow.classList.remove('force-inactive');
}

function setArrowButtonVisibility() {
  if (slider.scrollLeft === 0) {
    leftArrow.classList.add('force-inactive');
  } else {
    leftArrow.classList.remove('force-inactive');
  }
  if (slider.scrollLeft + slider.offsetWidth + 1 >= slider.scrollWidth) {
    rightArrow.classList.add('force-inactive');
  } else {
    rightArrow.classList.remove('force-inactive');
  }
}

function initSliderHandlers() {
  // When left arrow is clicked
  if (leftArrow) {
    leftArrow.addEventListener('click', scrollLeft);
  }
  // When right arrow is clicked
  if (rightArrow) {
    rightArrow.addEventListener('click', scrollRight);
  }
  // When slider is scrolled
  slider.addEventListener('scroll', setArrowButtonVisibility);
  window.addEventListener('resize', setArrowButtonVisibility);
}

function filterHandlers() {
  document
    .querySelector('#ow-apply-filter')
    .addEventListener('click', function () {
      const selectedInputs = document.querySelectorAll(
        '.filter-options input:checked'
      );
      // Create params map which knows about the last applied filters
      var path = window.location.href.split('?');
      var paramsMap = {};
      if (path.length > 1) {
        // Only if path contains query params
        path[1].split('&').map(function (param) {
          const [name, val] = param.split('=');
          paramsMap[name] = val;
        });
      }
      var qs = Object.assign({}, paramsMap);
      // qs will be modified according to the last applied filters
      // and current filters that need to be applied
      selectedInputs.forEach(function (selectedInput) {
        let value = selectedInput.value;
        // create params map for each option
        let currParamsMap = {};
        value
          .substring(1)
          .split('&')
          .forEach(function (param) {
            if (param != '') {
              let [name, val] = param.split('=');
              currParamsMap[name] = val;
            }
          });
        Object.keys(paramsMap).forEach(function (key) {
          /*
            LOGIC: 
              For any filter if we check the values present in the options available
              for it, we will notice that only its options have the different pararms
              that can change or remove from currently applied filter but all other
              options of other filters always remain same.
          */
          if (key in qs) {
            if (key in currParamsMap) {
              if (currParamsMap[key] != paramsMap[key]) {
                qs[key] = currParamsMap[key];
              }
            } else {
              delete qs[key];
            }
          }
          delete currParamsMap[key];
        });
        Object.keys(currParamsMap).forEach(function (key) {
          // Add if any new filter is applied
          qs[key] = currParamsMap[key];
        });
      });
      var queryParams = '';
      if (Object.keys(qs).length) {
        queryParams = '?' + Object.keys(qs).map(function (q) {
          return `${q}=${qs[q]}`;
        }).join('&');
      }
      window.location.href = window.location.pathname + queryParams;
    });
}
