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
});
