'use strict';
const owContainer = document.getElementById('container');
const owMenu = document.getElementById('menu');
const owMainContent = document.getElementById('main-content');
const owMenuToggle = document.querySelector('.menu-toggle');
const owHamburger = document.querySelector('.hamburger');
const owNav = document.querySelector('#menu .nav');
const owLabel = document.querySelector('.special-label');
var owGroupHead;
(function () {
  setMenu();
  initMenuGroupClickListener();
  initToggleMenuHandlers();
  initAccountViewHandler();
  initToolTipHandlers();
  initMenuHelpers();
})();

function isMenuClose() {
  var windowWidth = window.innerWidth;
  var isToggleState = (document.querySelector('.toggle-menu') && true) || false;
  return (
    windowWidth > 768 &&
    ((isToggleState && windowWidth > 1024) ||
      (!isToggleState && windowWidth <= 1024))
  );
}

function initMenuGroupClickListener() {
  let mgHeads = document.querySelectorAll('.mg-head');
  mgHeads.forEach(function (mgHead) {
    // Handle click on menu group
    mgHead.addEventListener('click', function (e) {
      e.stopPropagation();
      var currentActiveGroup = document.querySelector('.menu-group.active');
      var dropdown = mgHead.nextElementSibling;
      if (isMenuClose()) {
        // Only when menu is close
        var elementPosY = mgHead.offsetTop;
        var navScrollPos = owNav.scrollTop;
        var dropdownHeight = dropdown.offsetHeight;
        if (elementPosY - navScrollPos + dropdownHeight < window.innerHeight) {
          // Sufficient space to show dropdown at the right of menu icon
          dropdown.style.top = elementPosY - navScrollPos + 'px';
        } else {
          // Not sufficient space to show dropdown at the right of menu icon
          dropdown.style.top =
            elementPosY - navScrollPos - dropdownHeight + 10 + 'px';
        }
        if (owGroupHead && owGroupHead === mgHead) {
          // Hide the special label
          owLabel.classList.remove('show-sp-label');
        }
      }
      // Hide dropdown of current active menu group
      if (currentActiveGroup && currentActiveGroup !== mgHead.parentElement) {
        currentActiveGroup.classList.remove('active');
      }
      e.target.parentElement.classList.toggle('active');
      if (!e.target.parentElement.classList.contains('active')) {
        dropdown.style = '';
      }
    });
  });
  // Handle click out side the current active menu group
  document.addEventListener('click', function (e) {
    var currentActiveGroup = document.querySelector('.menu-group.active');
    if (currentActiveGroup && !currentActiveGroup.contains(e.target)) {
      currentActiveGroup.classList.remove('active');
      currentActiveGroup.querySelector('.mg-dropdown').style = '';
    }
  });
}

function initMenuHelpers() {
  /*
  It help in showing menu group dropdown and 
  menu element label when menu is close
  */
  var menuItems = document.querySelectorAll('.menu-item');
  var menuGroupHeads = document.querySelectorAll('.mg-head');
  function showLabel(label, element) {
    if (isMenuClose()) {
      // Only when menu is close
      var elementPosY = element.offsetTop;
      var navScrollPos = owNav.scrollTop;
      owLabel.innerText = label;
      owLabel.classList.add('show-sp-label');
      owLabel.style.top = elementPosY - navScrollPos + 10 + 'px';
    }
  }
  function hideLabel(e) {
    e.stopPropagation();
    owGroupHead = null;
    owLabel.classList.remove('show-sp-label');
  }
  function showLabelHandler(e) {
    e.stopPropagation();
    var element = e.target;
    owGroupHead = element;
    var currentActiveGroup = document.querySelector('.menu-group.active');
    if (
      currentActiveGroup &&
      currentActiveGroup.querySelector('.mg-head') === element
    ) {
      return;
    }
    var labelText = element.querySelector('.menu-label').innerText;
    showLabel(labelText, element);
  }
  menuItems.forEach(function (item) {
    item.addEventListener('mouseenter', showLabelHandler);
    item.addEventListener('mouseleave', hideLabel);
  });
  menuGroupHeads.forEach(function (item) {
    item.addEventListener('mouseenter', showLabelHandler);
    item.addEventListener('mouseleave', hideLabel);
  });
  function menuNavScollHandler() {
    // Hide menu group dropdown and special label
    // when menu is scrolled
    var currentActiveGroup = document.querySelector('.menu-group.active');
    var label = document.querySelector('.show-sp-label');
    if (currentActiveGroup && isMenuClose()) {
      currentActiveGroup.classList.remove('active');
      currentActiveGroup.querySelector('.mg-dropdown').style = '';
    }
    if (label) {label.classList.remove('show-sp-label');}
  }
  if (owNav) {owNav.addEventListener('scroll', menuNavScollHandler);}
  // Hide dropdown when window is resized
  window.addEventListener('resize', function () {
    var currentActiveGroup = document.querySelector('.menu-group.active');
    if (currentActiveGroup) {
      currentActiveGroup.classList.remove('active');
      currentActiveGroup.querySelector('.mg-dropdown').style = '';
    }
  });
}

function setMenu() {
  let openMenu = localStorage.getItem('ow-menu');
  if (!owMenu) {
    owMainContent.style.marginLeft = '0px';
  } else if (window.innerWidth > 1024) {
    if (openMenu === null) {
      // When user vists site first time. Menu must be open for wide screen
      localStorage.setItem('ow-menu', true);
    } else if (openMenu === 'false') {
      // Close menu
      owContainer.classList.toggle('toggle-menu');
    }
  }
  setTimeout(function () {
    // Dont remove this. Transition fix
    if (owMenu) {(owMenu.style.transitionDuration = '0.3s');}
    owMainContent.style.transitionDuration = '0.3s';
  }, 1000);
}

function initToggleMenuHandlers() {
  function toggleMenuHandler() {
    owContainer.classList.toggle('toggle-menu');
    let isMenuOpen = localStorage.getItem('ow-menu');
    if (window.innerWidth > 1024) {
      if (isMenuOpen === 'false') {
        isMenuOpen = true;
      } else {
        isMenuOpen = false;
      }
      localStorage.setItem('ow-menu', isMenuOpen);
    }
  }
  if (owMenuToggle) {owMenuToggle.addEventListener('click', toggleMenuHandler);}
  if (owHamburger) {owHamburger.addEventListener('click', toggleMenuHandler);}
}

function initAccountViewHandler() {
  var accountMenu = document.querySelector('.account-menu');
  var accountToggle = document.querySelector('.account-button');
  // When account button is clicked
  if (accountToggle) {
    accountToggle.addEventListener('click', function (e) {
      e.stopPropagation();
      accountMenu.classList.toggle('hide');
    });
  }
  // When clicked outside the account button
  document.addEventListener('click', function (e) {
    e.stopPropagation();
    var target = e.target;
    if (accountMenu && !accountMenu.contains(target)) {
      accountMenu.classList.add('hide');
    }
  });
}

function initToolTipHandlers() {
  // Tooltips shown only on narrow screen
  var tooltips = document.querySelectorAll('.tooltip-sm');
  function mouseLeaveHandler(e) {
    var tooltipText = e.target.getAttribute('tooltip-data');
    e.target.setAttribute('title', tooltipText);
    e.target.removeAttribute('tooltip-data');
    removeMouseLeaveListner(e.target);
  }
  function removeMouseLeaveListner(tooltip) {
    tooltip.removeEventListener('mouseleave', mouseLeaveHandler);
  }
  tooltips.forEach(function (tooltip) {
    tooltip.addEventListener('mouseenter', function () {
      if (window.innerWidth > 768) {
        var tooltipText = tooltip.getAttribute('title');
        tooltip.removeAttribute('title');
        tooltip.setAttribute('tooltip-data', tooltipText);
        tooltip.addEventListener('mouseleave', mouseLeaveHandler);
      }
    });
  });
}
