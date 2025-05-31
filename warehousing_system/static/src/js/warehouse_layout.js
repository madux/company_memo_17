/**
 * Warehouse Layout JavaScript with Persistent Sidebar State
 * (No manual “.active” toggling on click—rely on server’s current_page)
 */
$(document).ready(function() {
    const sidebar        = $('#sidebar');
    const mainContent    = $('#mainContent');
    const sidebarToggle  = $('#sidebarToggle');
    const sidebarOverlay = $('#sidebarOverlay');
    
    // storage keys:
    const SIDEBAR_STATE_KEY  = 'warehouse_sidebar_state';
    const SIDEBAR_MOBILE_KEY = 'warehouse_sidebar_mobile';

    // 1) Read from localStorage/sessionStorage to restore state
    function getSidebarState() {
        try {
            if (typeof(Storage) !== "undefined") {
                return {
                    isCollapsed:  localStorage.getItem(SIDEBAR_STATE_KEY) === 'collapsed',
                    isMobileOpen: localStorage.getItem(SIDEBAR_MOBILE_KEY) === 'open'
                };
            }
        } catch (_) { /* ignore */ }
        try {
            if (typeof(sessionStorage) !== "undefined") {
                return {
                    isCollapsed:  sessionStorage.getItem(SIDEBAR_STATE_KEY) === 'collapsed',
                    isMobileOpen: sessionStorage.getItem(SIDEBAR_MOBILE_KEY) === 'open'
                };
            }
        } catch (_) { /* ignore */ }
        // default:
        return { isCollapsed: false, isMobileOpen: false };
    }

    // 2) Write to localStorage/sessionStorage
    function saveSidebarState(isCollapsed, isMobileOpen) {
        try {
            if (typeof(Storage) !== "undefined") {
                localStorage.setItem(SIDEBAR_STATE_KEY,  isCollapsed  ? 'collapsed' : 'expanded');
                localStorage.setItem(SIDEBAR_MOBILE_KEY, isMobileOpen ? 'open'      : 'closed');
                return;
            }
        } catch (_) { /* ignore */ }
        try {
            if (typeof(sessionStorage) !== "undefined") {
                sessionStorage.setItem(SIDEBAR_STATE_KEY,  isCollapsed  ? 'collapsed' : 'expanded');
                sessionStorage.setItem(SIDEBAR_MOBILE_KEY, isMobileOpen ? 'open'      : 'closed');
            }
        } catch (_) { /* ignore */ }
    }

    // 3) On first load, restore whichever state was saved
    function initializeSidebarState() {
        const state = getSidebarState();
        if (window.innerWidth <= 768) {
            // For small screens, if “mobileOpen” was true, show it:
            if (state.isMobileOpen) {
                sidebar.addClass('show');
                sidebarOverlay.addClass('show');
            }
        } else {
            // For desktop screens, if “collapsed” was true, collapse it:
            if (state.isCollapsed) {
                sidebar.addClass('collapsed');
                mainContent.addClass('expanded');
            }
        }
    }

    // 4) Toggling logic—store into localStorage each time
    function toggleSidebar() {
        if (window.innerWidth <= 768) {
            // Mobile: just toggle “.show”
            const isCurrentlyOpen = sidebar.hasClass('show');
            sidebar.toggleClass('show');
            sidebarOverlay.toggleClass('show');
            saveSidebarState(false, !isCurrentlyOpen);
        } else {
            // Desktop: toggle “.collapsed” + “.expanded”
            const isCurrentlyCollapsed = sidebar.hasClass('collapsed');
            sidebar.toggleClass('collapsed');
            mainContent.toggleClass('expanded');
            saveSidebarState(!isCurrentlyCollapsed, false);
        }
    }

    sidebarToggle.on('click', function() {
        toggleSidebar();
    });

    sidebarOverlay.on('click', function() {
        // clicking overlay always closes mobile sidebar
        sidebar.removeClass('show');
        sidebarOverlay.removeClass('show');
        saveSidebarState(false, false);
    });

    $(window).on('resize', function() {
        const state = getSidebarState();
        if (window.innerWidth > 768) {
            // switching to desktop → remove mobile classes
            sidebar.removeClass('show');
            sidebarOverlay.removeClass('show');
            if (state.isCollapsed) {
                sidebar.addClass('collapsed');
                mainContent.addClass('expanded');
            }
        } else {
            // switching to mobile → remove “.collapsed / .expanded”
            sidebar.removeClass('collapsed');
            mainContent.removeClass('expanded');
        }
    });

    // 5) *** NO MANUAL “.active” ON CLICK *** ***
    // Because each link already has t-att-class="'nav-link' + (' active' if current_page == '…').
    // So the server’s value of current_page will be applied on page load.
    //
    // If you still want a very brief “visual feedback” before reload, you
    // can do something like “$(this).addClass('active')” here—but it will
    // immediately be overwritten by the server’s HTML anyway.

    // 6) If you want one‐time fallback (in case a template forgot to inject current_page),
    //    you can run this on document.ready *after* initializeSidebarState():
    function fallbackSetActiveByPath() {
        // Remove everything first.
        $('.nav-link').removeClass('active');
        const current = window.location.pathname;
        $('.nav-link').each(function() {
            const href = $(this).attr('href');
            if ((current === '/warehouse' || current === '/warehouse/') && href === '/warehouse/dashboard') {
                $(this).addClass('active');
                return;
            }
            if (current === href || (href !== '/warehouse' && href !== '/' && current.startsWith(href))) {
                $(this).addClass('active');
            }
        });
    }

    // 7) Finally, smooth‐scroll and ESC‐to‐close if needed:
    $('a[href^="#"]').on('click', function(e) {
        e.preventDefault();
        const target = $(this.getAttribute('href'));
        if (target.length) {
            $('html, body').stop().animate({
                scrollTop: target.offset().top
            }, 1000);
        }
    });
    $(document).on('keydown', function(e) {
        if (e.key === 'Escape' && window.innerWidth <= 768) {
            sidebar.removeClass('show');
            sidebarOverlay.removeClass('show');
            saveSidebarState(false, false);
        }
    });

    $('.sidebar-brand').on('click', function(e) {
        e.preventDefault();
        // We rely on the server to highlight “dashboard” next
        window.location.href = '/warehouse/dashboard';
    });

    // 8) Run initializers in the correct order:
    initializeSidebarState();
    // If your XML always injects “.active” via current_page, you do NOT need fallback:
    // fallbackSetActiveByPath();

    // If there is no “current_page” injected for some reason, you can uncomment the next line:
    // fallbackSetActiveByPath();
});