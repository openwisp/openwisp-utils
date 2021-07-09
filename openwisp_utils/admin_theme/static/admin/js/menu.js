'use strict';
const owContainer = document.getElementById('container');
const owMenu = document.getElementById('menu');
const owMainContent = document.getElementById('main-content');
const owMenuToggle = document.querySelector('.menu-toggle');
const owHamburger = document.querySelector('.hamburger');

(function () {
  setMenu();
  initMenuGroupClickListener();
  initToggleMenuHandlers();
  initAccountViewHandler();
  initToolTipHandlers();
})();

function initMenuGroupClickListener() {
  let mgHeads = document.querySelectorAll('.mg-head');
  mgHeads.forEach(function (mgHead) {
    // Handle click on menu group
    mgHead.addEventListener('click', function (e) {
      e.stopPropagation();
      var currentActiveGroup = document.querySelector('.menu-group.active');
      if (currentActiveGroup && currentActiveGroup !== mgHead.parentElement) {
        currentActiveGroup.classList.remove('active');
      }
      e.target.parentElement.classList.toggle('active');
    });
  });
  // Handle click out side the current active menu group
  document.addEventListener('click', function (e) {
    var currentActiveGroup = document.querySelector('.menu-group.active');
    if (currentActiveGroup && !currentActiveGroup.contains(e.target)) {
      currentActiveGroup.classList.remove('active');
    }
  });
}

function setMenu() {
  let openMenu = localStorage.getItem('ow-menu');
  if (window.innerWidth > 1024) {
    if (openMenu === null) {
      // User visits first time. Keep open menu
      localStorage.setItem('ow-menu', true);
      owContainer.classList.toggle('toggle-menu');
    } else if (openMenu === 'false') {
      // Close the menu
      owContainer.classList.toggle('toggle-menu');
    }
  }
  setTimeout(function () {
    // Transition fix: Add transition to menu and main content
    // after some time.
    if (owMenu) {
      owMenu.style.transitionDuration = '0.3s';
    }
    owMainContent.style.transitionDuration = '0.3s';
  }, 1000);
}

function initToggleMenuHandlers() {
  function toggleMenuHandler() {
    owContainer.classList.toggle('toggle-menu');
    let isMenuOpen = localStorage.getItem('ow-menu');
    if (window.innerWidth > 1024) {
      localStorage.setItem('ow-menu', isMenuOpen === 'true' ? false : true);
    }
  }
  if (owMenuToggle && owContainer) {
    owMenuToggle.addEventListener('click', toggleMenuHandler);
  }
  if (owHamburger && owContainer) {
    owHamburger.addEventListener('click', toggleMenuHandler);
  }
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
