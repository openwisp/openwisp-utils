(function($) {
    'use strict';
    var openMenu = localStorage.getItem('ow-menu');
    if (window.innerWidth > 768) {
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
    function toggleMenuHandler(){
        $('#container').toggleClass('toggle-menu');
        var currValue = localStorage.getItem('ow-menu');
        if (window.innerWidth > 768) {
            if (currValue === 'false') {
                currValue = true;
            } else {
                currValue = false;
            }
            localStorage.setItem('ow-menu', currValue);
        }
    }
    $('.heading').on('click', function (e) {
        e.stopPropagation();
        var heading = e.target;
        ($(heading).parent()).toggleClass('active');
    });
    $('.menu-toggle').on('click', toggleMenuHandler);
    $('#header-nav .user').on('click', toggleMenuHandler);
    $('.backdrop, .menu-close').on('click', function () {
        $('#container').toggleClass('toggle-menu');
    });
})(django.jQuery);
