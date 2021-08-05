'use strict';
const owContainer = document.getElementById('container');
const owMenu = document.getElementById('menu');
const owMainContent = document.getElementById('main-content');
const owMenuToggle = document.querySelector('.menu-toggle');
const owHamburger = document.querySelector('.hamburger');
const menuBackdrop = document.querySelector('.menu-backdrop');
const owNav = document.querySelector('#menu .nav');
const MenuTransitionTime = '0.1s';

(function () {
  setMenu();
  initGroupViewHandlers();
  initToggleMenuHandlers();
  initAccountViewHandler();
  initToolTipHandlers();
  initResizeScreenHelpers();
  showActiveItems();
})();

function Window() {
  /*
    To prevent editing of variables from console.
    Because variables are used to manage state of window
  */
  var windowWidth = window.innerWidth;
  this.setWindowWidth = function (size) {
    windowWidth = size;
  };
  this.getWindowWidth = function () {
    return windowWidth;
  };
}

function closeActiveGroup(group = null) {
  if (group === null) {
    group = document.querySelector('.menu-group.active');
  }
  if (group) {
    group.classList.remove('active');
    group.querySelector('.mg-dropdown').style = '';
  }
}

function isMenuOpen() {
  return !owContainer.classList.contains('toggle-menu');
}

function initResizeScreenHelpers() {
  function changeMenuState(owWindow) {
    var currentWidth = window.innerWidth;
    var isMenuOpen = !owContainer.classList.contains('toggle-menu');
    if (currentWidth <= 1024) {
      if (owWindow.getWindowWidth() > 1024 && isMenuOpen) {
        // close window
        closeActiveGroup();
        owContainer.classList.add('toggle-menu');
        owWindow.setWindowWidth(currentWidth);
        setMenuToggleText();
      }
    } else if (owWindow.getWindowWidth() <= 1024) {
      // when window width is greater than 1024px
      // work according to user last choice
      setMenuState();
      owWindow.setWindowWidth(currentWidth);
      setMenuToggleText();
    }
  }
  var owWindow = new Window();
  window.addEventListener('resize', function () {
    changeMenuState(owWindow);
  });
}

function initGroupViewHandlers() {
  var mgHeads = document.querySelectorAll('.mg-head');
  mgHeads.forEach(function (mgHead) {
    // Handle click on menu group
    mgHead.addEventListener('click', function (e) {
      e.stopPropagation();
      var currentActiveGroup = document.querySelector('.menu-group.active');
      if (currentActiveGroup && currentActiveGroup !== mgHead.parentElement) {
        closeActiveGroup(currentActiveGroup);
      }
      if (window.innerWidth > 768 && !isMenuOpen()) {
        var group = e.target.parentElement;
        var dropdown = group.querySelector('.mg-dropdown');
        if (!group.classList.contains('active')) {
          var groupPos = group.offsetTop;
          var scrolledBy = owNav.scrollTop;
          var dropdownHeight = group.querySelector('.mg-dropdown').offsetHeight;
          if (dropdownHeight + groupPos - scrolledBy >= window.innerHeight) {
            dropdown.style.top =
              groupPos - scrolledBy - dropdownHeight + 87 + 'px';
            setTimeout(function () {
              e.target.parentElement.classList.toggle('active');
              dropdown.style.top =
                groupPos - scrolledBy - dropdownHeight + 40 + 'px';
            }, 10);
          } else {
            dropdown.style.top = groupPos - scrolledBy + 47 + 'px';
            setTimeout(function () {
              e.target.parentElement.classList.toggle('active');
              dropdown.style.top = groupPos - scrolledBy + 'px';
            }, 10);
          }
        } else {
          closeActiveGroup(e.target.parentElement);
        }
        return;
      }
      e.target.parentElement.classList.toggle('active');
    });
    mgHead.addEventListener('mouseenter', function (e) {
      e.stopImmediatePropagation();
      if (window.innerWidth > 768 && !isMenuOpen()) {
        var group = e.target.parentElement;
        var groupPos = group.offsetTop;
        var scrolledBy = owNav.scrollTop;
        var label = e.target.querySelector('.label');
        label.style.top = groupPos - scrolledBy + 13 + 'px';
      }
    });
    mgHead.addEventListener('mouseleave', function (e) {
      if (window.innerWidth > 768 && !isMenuOpen()) {
        var label = e.target.querySelector('.label');
        label.style = '';
      }
    });
    document.querySelectorAll('.menu-item').forEach(function (item) {
      item.addEventListener('mouseenter', function (e) {
        e.stopImmediatePropagation();
        if (window.innerWidth > 768 && !isMenuOpen()) {
          var itemPos = item.offsetTop;
          var scrolledBy = owNav.scrollTop;
          var label = e.target.querySelector('.label');
          label.style.top = itemPos - scrolledBy + 13 + 'px';
        }
      });
      item.addEventListener('mouseleave', function (e) {
        var label = e.target.querySelector('.label');
        label.style = '';
      });
    });
  });
  // Handle click out side the current active menu group
  document.addEventListener('click', function (e) {
    var currentActiveGroup = document.querySelector('.menu-group.active');
    if (currentActiveGroup && !currentActiveGroup.contains(e.target)) {
      closeActiveGroup(currentActiveGroup);
    }
  });
  owNav.addEventListener('scroll', function () {
    if (!isMenuOpen()) {
      closeActiveGroup();
    }
  });
}

function setMenuState() {
  let openMenu = localStorage.getItem('ow-menu');
  if (window.innerWidth > 1024) {
    if (openMenu === null) {
      // User visits first time. Keep open menu
      localStorage.setItem('ow-menu', true);
      owContainer.classList.remove('toggle-menu');
    } else if (openMenu === 'true') {
      // Close the menu
      owContainer.classList.remove('toggle-menu');
    }
  }
}

function setMenuToggleText() {
  if (isMenuOpen()) {
    owMenuToggle.setAttribute('title', 'Minimize menu');
  } else {
    owMenuToggle.setAttribute('title', 'Maximize menu');
  }
}

function setMenu() {
  setMenuState();
  setMenuToggleText();
  setTimeout(function () {
    // Transition fix: Add transition to menu and main content
    // after some time.
    if (owMenu) {
      owMenu.style.transitionDuration = MenuTransitionTime;
    }
    if (owMainContent) {
      owMainContent.style.transitionDuration = MenuTransitionTime;
    }
    if (owMenuToggle) {
      owMenuToggle.style.transitionDuration = MenuTransitionTime;
    }
  }, 1000);
  setMenuToggleText();
}

function initToggleMenuHandlers() {
  function toggleMenuHandler() {
    owContainer.classList.toggle('toggle-menu');
    let isMenuOpen = localStorage.getItem('ow-menu');
    if (window.innerWidth > 1024) {
      localStorage.setItem('ow-menu', isMenuOpen === 'true' ? false : true);
    }
    setMenuToggleText();
  }
  if (owMenuToggle && owContainer) {
    owMenuToggle.addEventListener('click', toggleMenuHandler);
  }
  if (owHamburger && owContainer) {
    owHamburger.addEventListener('click', toggleMenuHandler);
  }
  // Close menu when backdrop is clicked
  menuBackdrop.addEventListener('click', function (e) {
    e.stopPropagation();
    owContainer.classList.toggle('toggle-menu');
  });
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

function showActiveItems() {
  if (!owMenu) { return; }
  var pathname = window.location.pathname;
  const regex = new RegExp(/[\d\w-]*\/change\//);
  pathname = pathname.replace(regex, '');
  var activeLink = document.querySelector(`.nav a[href="${pathname}"]`);
  if (!activeLink) { return; }
  activeLink.classList.add('active');
  if (activeLink.classList.contains('mg-link')) {
    var group = activeLink.closest('.menu-group');
    group.classList.add('active-mg');
    if (isMenuOpen()) {
      group.classList.add('active');
    }
  }
}
