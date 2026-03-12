/* ============================================
   AOG INDIA — JavaScript
   Navbar scroll · Mobile menu · Smooth scroll
   Counter animation · AOS init
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {

  // ─── AOS Init ───────────────────────────
  AOS.init({
    duration: 700,
    easing: 'ease-out-cubic',
    once: true,
    offset: 80
  });

  // ─── Elements ───────────────────────────
  const navbar = document.getElementById('navbar');
  const navLinks = document.getElementById('navLinks');
  const navHamburger = document.getElementById('navHamburger');
  const navOverlay = document.getElementById('navOverlay');
  const allNavAnchors = navLinks.querySelectorAll('a');

  // ─── Navbar Scroll Effect ───────────────
  const handleScroll = () => {
    if (window.scrollY > 60) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }

    // Active link highlight
    const sections = document.querySelectorAll('section[id]');
    let current = '';
    sections.forEach(section => {
      const top = section.offsetTop - 120;
      if (window.scrollY >= top) {
        current = section.getAttribute('id');
      }
    });
    allNavAnchors.forEach(a => {
      a.classList.remove('active');
      if (a.getAttribute('href') === '#' + current) {
        a.classList.add('active');
      }
    });
  };

  window.addEventListener('scroll', handleScroll, { passive: true });
  handleScroll(); // initial call

  // ─── Mobile Menu Toggle ─────────────────
  const toggleMenu = () => {
    navHamburger.classList.toggle('active');
    navLinks.classList.toggle('open');
    navOverlay.classList.toggle('active');
    document.body.style.overflow = navLinks.classList.contains('open') ? 'hidden' : '';
  };

  navHamburger.addEventListener('click', toggleMenu);
  navOverlay.addEventListener('click', toggleMenu);

  // Close menu on link click
  allNavAnchors.forEach(a => {
    a.addEventListener('click', () => {
      if (navLinks.classList.contains('open')) {
        toggleMenu();
      }
    });
  });

  // ─── Counter Animation ─────────────────
  const formatNumber = (n) => {
    if (n >= 1000000) return (n / 1000000).toFixed(0) + 'M+';
    if (n >= 1000) return (n / 1000).toFixed(0) + 'K+';
    return n.toString();
  };

  const animateCounter = (el) => {
    const target = parseInt(el.getAttribute('data-count'));
    const noFormat = el.hasAttribute('data-no-format');
    const duration = 2000;
    const startTime = performance.now();

    const update = (now) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(eased * target);

      if (noFormat) {
        el.textContent = current;
      } else {
        el.textContent = formatNumber(current);
      }

      if (progress < 1) {
        requestAnimationFrame(update);
      }
    };

    requestAnimationFrame(update);
  };

  // Use IntersectionObserver for counters
  const statValues = document.querySelectorAll('.stat-value[data-count]');
  if (statValues.length > 0) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          animateCounter(entry.target);
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.5 });

    statValues.forEach(el => observer.observe(el));
  }

  // ─── Contact Form (basic) ──────────────
  const contactForm = document.getElementById('contactForm');
  if (contactForm) {
    contactForm.addEventListener('submit', (e) => {
      // If using Formspree, let the default action happen.
      // If the action URL still has placeholder, prevent and alert.
      const action = contactForm.getAttribute('action');
      if (action.includes('YOUR_FORM_ID')) {
        e.preventDefault();
        alert('Contact form is not configured yet. Please email us directly at partnerships@aogindia.com');
      }
    });
  }

});
