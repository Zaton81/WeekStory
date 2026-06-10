/**
 * WeekStory Frontend Interactions helper
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(() => {
                alert.remove();
            }, 500);
        }, 5000);

        // Bind manual dismiss button
        const closeBtn = alert.querySelector('.alert-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                alert.remove();
            });
        }
    });

    // 2. Tab switcher for social media posts dashboard
    window.switchTab = function(event, platformId) {
        // Get all tabs and contents in the container
        const tabsContainer = event.currentTarget.closest('.social-dashboard');
        if (!tabsContainer) return;

        const tabs = tabsContainer.querySelectorAll('.social-tab');
        const contents = tabsContainer.querySelectorAll('.tab-content');

        // Deactivate all tabs and hide all contents
        tabs.forEach(t => t.classList.remove('active'));
        contents.forEach(c => c.classList.remove('active'));

        // Activate selected tab and show content
        event.currentTarget.classList.add('active');
        const targetContent = tabsContainer.querySelector(`#post-${platformId}`);
        if (targetContent) {
            targetContent.classList.add('active');
        }
    };

    // 3. Toggle Categories Dropdown in Navbar
    const categoriesBtn = document.getElementById("categoriesDropdownBtn");
    const categoriesMenu = document.getElementById("categoriesDropdownMenu");

    if (categoriesBtn && categoriesMenu) {
        categoriesBtn.addEventListener("click", (e) => {
            e.preventDefault();
            const isShown = categoriesMenu.classList.contains("show") || categoriesMenu.style.display === "block";
            if (isShown) {
                categoriesMenu.style.display = "none";
                categoriesMenu.classList.remove("show");
            } else {
                categoriesMenu.style.display = "block";
                categoriesMenu.classList.add("show");
            }
        });

        document.addEventListener("click", (e) => {
            if (!categoriesBtn.contains(e.target) && !categoriesMenu.contains(e.target)) {
                categoriesMenu.style.display = "none";
                categoriesMenu.classList.remove("show");
            }
        });
    }

    // 4. Cookies Consent Banner Manager
    const cookieBanner = document.getElementById("cookie-consent-banner");
    const acceptCookiesBtn = document.getElementById("accept-cookies-btn");

    if (cookieBanner && acceptCookiesBtn) {
        const cookiesAccepted = document.cookie.split('; ').find(row => row.startsWith('cookies_accepted='));
        if (!cookiesAccepted) {
            cookieBanner.style.display = 'block';
        }

        acceptCookiesBtn.addEventListener("click", () => {
            // Set cookie for 1 year (31536000 seconds)
            document.cookie = "cookies_accepted=true; max-age=31536000; path=/";
            cookieBanner.style.animation = 'none';
            cookieBanner.style.opacity = '0';
            cookieBanner.style.transition = 'opacity 0.4s ease';
            setTimeout(() => {
                cookieBanner.style.display = 'none';
            }, 400);
        });
    }
});
