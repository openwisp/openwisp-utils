'use strict';
const owContainer = document.getElementById('container');
const owMenu = document.getElementById("menu");
const owMainContent = document.getElementById("main-content");
const owMenuToggle = document.querySelector('.menu-toggle');

(function() {
  setMenu();
  initMenuGroupClickListener();
  initToggleMenuHandlers();
})();

function initMenuGroupClickListener() {
  let menuGroupTitles = document.querySelectorAll('.menu-group-title');
  menuGroupTitles.forEach(function(menuGroupTitle) {
    menuGroupTitle.addEventListener('click', function (e) {
      e.stopPropagation();
      e.target.parentElement.classList.toggle('active');
    });
  });
}

function setMenu() {
  let openMenu = localStorage.getItem('ow-menu');
  if (window.innerWidth > 1024) {
    if(openMenu === null){
      localStorage.setItem('ow-menu', true);
    } else if (openMenu === 'false') {
      owContainer.classList.toggle('toggle-menu');
    }
  }
  setTimeout(function () {
    owMenu.style.transitionDuration = "0.3s";
    owMainContent.style.transitionDuration = "0.3s";
  }, 1000);
}

function initToggleMenuHandlers() {
  function toggleMenuHandler(){
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
  owMenuToggle.addEventListener('click', toggleMenuHandler);
}
