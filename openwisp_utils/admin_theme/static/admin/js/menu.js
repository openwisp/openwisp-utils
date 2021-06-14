'use strict';
(function($) {
  setMenu($);
  initMenuGroupClickListner($);
  initToggleMenuHandlers($);
})(django.jQuery);

function initMenuGroupClickListner($) {
  $('.menu-group-title').on('click', function (e) {
    e.stopPropagation();
    var groupTitle = e.target;
    ($(groupTitle).parent()).toggleClass('active');
  });
}

function setMenu($) {
  var openMenu = localStorage.getItem('ow-menu');
  if (window.innerWidth > 1024) {
    if(openMenu === null){
      localStorage.setItem('ow-menu', true);
    } else if (openMenu === 'false') {
      $('#container').toggleClass('toggle-menu');
    }
  }
  setTimeout(function () {
    $('#menu').css('transition-duration', '0.3s');
    $('#main-content').css('transition-duration', '0.3s');
  }, 1000);
}

function initToggleMenuHandlers($) {
  function toggleMenuHandler(){
    $('#container').toggleClass('toggle-menu');
    var isMenuOpen = localStorage.getItem('ow-menu');
    if (window.innerWidth > 1024) {
      if (isMenuOpen === 'false') {
        isMenuOpen = true;
      } else {
        isMenuOpen = false;
      }
      localStorage.setItem('ow-menu', isMenuOpen);
    }
  }
  $('.menu-toggle').on('click', toggleMenuHandler);
}
