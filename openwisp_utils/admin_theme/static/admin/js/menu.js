window.addEventListener('load', function(){
  'use strict';
  var nav = document.getElementById('main-menu'),
      container = document.getElementById('container'),
      header = document.getElementById('header'),
  setHeightToMenu = function() {
    var windowHeight = window.innerHeight,
        pageHeight = container.offsetHeight,
        height = windowHeight;
    if (pageHeight > windowHeight) {
      height = pageHeight;
    }
    nav.style.height = (height - header.offsetHeight) + 'px';
    nav.style.marginTop = header.offsetHeight + 'px';
  };
  setHeightToMenu();
  window.addEventListener('resize', setHeightToMenu);
});
