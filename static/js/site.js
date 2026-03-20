(function () {
    document.body.classList.add('enhanced');

    const header = document.querySelector('.site-header');
    const onScroll = function () {
        if (!header) {
            return;
        }
        if (window.scrollY > 12) {
            header.classList.add('is-scrolled');
        } else {
            header.classList.remove('is-scrolled');
        }
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });

    const revealNodes = document.querySelectorAll('.reveal');
    if (revealNodes.length) {
        const observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.16, rootMargin: '0px 0px -40px 0px' });

        revealNodes.forEach(function (node, index) {
            node.style.transitionDelay = String((index % 6) * 70) + 'ms';
            observer.observe(node);
        });
    }

    document.addEventListener('click', function (event) {
        document.querySelectorAll('.user-menu[open]').forEach(function (menu) {
            if (!menu.contains(event.target)) {
                menu.removeAttribute('open');
            }
        });
    });
}());

