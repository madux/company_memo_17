/**
 * Warehouse Layout JavaScript
 * Handles sidebar toggle functionality and navigation
 */

$(document).ready(function() {
    // Cache DOM elements
    const sidebar = $('#sidebar');
    const mainContent = $('#mainContent');
    const sidebarToggle = $('#sidebarToggle');
    const sidebarOverlay = $('#sidebarOverlay');

    /**
     * Handle sidebar toggle based on screen size
     */
    sidebarToggle.on('click', function() {
        if (window.innerWidth <= 768) {
            // Mobile behavior - show/hide sidebar with overlay
            sidebar.toggleClass('show');
            sidebarOverlay.toggleClass('show');
        } else {
            // Desktop behavior - collapse/expand sidebar
            sidebar.toggleClass('collapsed');
            mainContent.toggleClass('expanded');
        }
    });

    /**
     * Close sidebar when clicking overlay (mobile only)
     */
    sidebarOverlay.on('click', function() {
        sidebar.removeClass('show');
        sidebarOverlay.removeClass('show');
    });

    /**
     * Handle window resize events
     * Reset mobile classes when switching to desktop
     */
    $(window).on('resize', function() {
        if (window.innerWidth > 768) {
            sidebar.removeClass('show');
            sidebarOverlay.removeClass('show');
        }
    });

    /**
     * Active navigation link highlighting
     * Automatically highlights the current page in the navigation
     */
    function setActiveNavLink() {
        const currentPath = window.location.pathname;
        
        $('.nav-link').each(function() {
            const href = $(this).attr('href');
            
            // Remove active class from all links first
            $(this).removeClass('active');
            
            // Add active class if current path matches or starts with the link href
            if (currentPath === href || (href !== '/' && currentPath.startsWith(href))) {
                $(this).addClass('active');
            }
        });
    }

    // Set active link on page load
    setActiveNavLink();

    /**
     * Optional: Add smooth scrolling for anchor links
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
     * Optional: Close mobile sidebar when clicking nav links
     */
    $('.nav-link').on('click', function() {
        if (window.innerWidth <= 768) {
            sidebar.removeClass('show');
            sidebarOverlay.removeClass('show');
        }
    });

    /**
     * Optional: Add keyboard navigation support
     */
    $(document).on('keydown', function(e) {
        // ESC key closes mobile sidebar
        if (e.key === 'Escape' && window.innerWidth <= 768) {
            sidebar.removeClass('show');
            sidebarOverlay.removeClass('show');
        }
    });
});