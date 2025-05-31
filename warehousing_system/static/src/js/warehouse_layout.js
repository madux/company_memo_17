/**
 * Warehouse Layout JavaScript
 * Handles sidebar toggle functionality and navigation
 */

$(document).ready(function() {
    const sidebar = $('#sidebar');
    const mainContent = $('#mainContent');
    const sidebarToggle = $('#sidebarToggle');
    const sidebarOverlay = $('#sidebarOverlay');

    
    sidebarToggle.on('click', function() {
        if (window.innerWidth <= 768) {
            sidebar.toggleClass('show');
            sidebarOverlay.toggleClass('show');
        } else {
            sidebar.toggleClass('collapsed');
            mainContent.toggleClass('expanded');
        }
    });

    
    sidebarOverlay.on('click', function() {
        sidebar.removeClass('show');
        sidebarOverlay.removeClass('show');
    });

    
    $(window).on('resize', function() {
        if (window.innerWidth > 768) {
            sidebar.removeClass('show');
            sidebarOverlay.removeClass('show');
        }
    });

    
    // function setActiveNavLink() {
    //     const currentPath = window.location.pathname;
        
    //     $('.nav-link').each(function() {
    //         const href = $(this).attr('href');
            
    //         // Remove active class from all links first
    //         $(this).removeClass('active');
            
    //         // Add active class if current path matches or starts with the link href
    //         if (currentPath === href || (href !== '/' && currentPath.startsWith(href))) {
    //             $(this).addClass('active');
    //         }
    //     });
    // }
    function setActiveNavLink() {
        const currentPath = window.location.pathname;
        
        $('.nav-link').removeClass('active');
        
        if (typeof window.current_page !== 'undefined') {
            return;
        }
        $('.nav-link').each(function() {
            const href = $(this).attr('href');
            
            if ((currentPath === '/warehouse' || currentPath === '/warehouse/') && href === '/warehouse/dashboard') {
                $(this).addClass('active');
                return;
            }  
            if (currentPath === href || (href !== '/warehouse' && href !== '/' && currentPath.startsWith(href))) {
                $(this).addClass('active');
            }
        });
    }

    // Set active link on page load
    setActiveNavLink();

    //************************ */
    $('.nav-link').on('click', function(e) {
        const href = $(this).attr('href');
        
        $('.nav-link').removeClass('active');
        
        $(this).addClass('active');
        
        if (window.innerWidth <= 768) {
            sidebar.removeClass('show');
            sidebarOverlay.removeClass('show');
        }
    });
    //*************************** */

    /**
     * Smooth scrolling for anchor links
     */
    $('a[href^="#"]').on('click', function(e) {
        e.preventDefault();
        
        const target = $(this.getAttribute('href'));
        if (target.length) {
            $('html, body').stop().animate({
                scrollTop: target.offset().top
            }, 1000);
        }
    });

    /**
     * Close mobile sidebar when clicking nav links
     */
    $('.nav-link').on('click', function() {
        if (window.innerWidth <= 768) {
            sidebar.removeClass('show');
            sidebarOverlay.removeClass('show');
        }
    });

    /**
     * Keyboard navigation support
     */
    $(document).on('keydown', function(e) {
        // ESC key closes mobile sidebar
        if (e.key === 'Escape' && window.innerWidth <= 768) {
            sidebar.removeClass('show');
            sidebarOverlay.removeClass('show');
        }
    });

    $('.sidebar-brand').on('click', function(e) {
        e.preventDefault();
        
        $('.nav-link').removeClass('active');
        
        $('a[href="/warehouse/dashboard"]').addClass('active');
        window.location.href = '/warehouse/dashboard';
    });

    function initializePage() {
        const hasActiveLink = $('.nav-link.active').length > 0;
        if (!hasActiveLink) {
            $('a[href="/warehouse/dashboard"]').addClass('active');
        }
    }

    initializePage();
});