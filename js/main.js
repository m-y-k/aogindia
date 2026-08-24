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

  // ─── Partners Dropdown ──────────────────
  const navDropdown = document.getElementById('navDropdown');
  const navDropdownToggle = document.getElementById('navDropdownToggle');
  if (navDropdown && navDropdownToggle) {
    // Toggle on click (keyboard / touch friendly)
    navDropdownToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      const isOpen = navDropdown.classList.toggle('open');
      navDropdownToggle.setAttribute('aria-expanded', isOpen);
    });
    // Close when clicking outside
    document.addEventListener('click', (e) => {
      if (!navDropdown.contains(e.target)) {
        navDropdown.classList.remove('open');
        navDropdownToggle.setAttribute('aria-expanded', 'false');
      }
    });
    // Close dropdown when mobile menu closes
    navOverlay.addEventListener('click', () => {
      navDropdown.classList.remove('open');
    });
  }

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

  // ─── Contact Form Dynamic & Logic ───────────
  const contactForm = document.getElementById('contactForm');
  if (contactForm) {
    // Utility to slide & fade elements dynamically and set required attribute
    const toggleGroup = (id, show, required = false) => {
      const el = document.getElementById(id);
      if (!el) return;
      
      if (show) {
        el.classList.add('visible');
      } else {
        el.classList.remove('visible');
      }

      // Handle inputs required attribute
      const inputs = el.querySelectorAll('input, select, textarea');
      inputs.forEach(input => {
        const label = el.querySelector(`label[for="${input.id}"]`);
        if (show && required) {
          input.setAttribute('required', '');
          if (label) label.classList.add('required-label');
        } else {
          input.removeAttribute('required');
          if (label) label.classList.remove('required-label');
        }
      });
    };

    const updateFormFields = () => {
      const userType = document.getElementById('userType')?.value || '';
      const brandQueryType = document.getElementById('brandQueryType')?.value || '';
      const creatorQueryType = document.getElementById('creatorQueryType')?.value || '';
      const discovery = document.getElementById('discovery')?.value || '';
      const messageLabel = document.getElementById('messageLabel');
      const messageInput = document.getElementById('message');

      // 1. Brand vs Creator toggling
      if (userType === 'brand') {
        toggleGroup('group-brand-name', true, true);
        toggleGroup('group-brand-website', true, true); // Website URL is now mandatory for Brands
        toggleGroup('group-brand-query', true, true);

        toggleGroup('group-creator-channel', false);
        toggleGroup('group-creator-query', false);
        toggleGroup('group-creator-link', false);
        toggleGroup('group-creator-subs', false);

        // Budget is required for Campaigns and Sponsorships
        const needsBudget = (brandQueryType === 'Campaign Collaboration' || brandQueryType === 'Long-term Sponsorship');
        toggleGroup('group-brand-budget', needsBudget, needsBudget);

        if (messageLabel) messageLabel.textContent = 'Campaign Details & Goals';
        if (messageInput) messageInput.placeholder = 'Tell us about your brand goals, target audience, timelines, and deliverables...';
      } else if (userType === 'creator') {
        toggleGroup('group-brand-name', false);
        toggleGroup('group-brand-website', false);
        toggleGroup('group-brand-query', false);
        toggleGroup('group-brand-budget', false);

        toggleGroup('group-creator-channel', true, true);
        toggleGroup('group-creator-query', true, true);
        toggleGroup('group-creator-link', true, true); // Channel Link is now mandatory for Creators
        toggleGroup('group-creator-subs', true, true); // Subscriber Count is now mandatory for Creators

        if (messageLabel) messageLabel.textContent = 'Channel & Growth Details';
        if (messageInput) messageInput.placeholder = 'Tell us about your audience, your primary games, and what you hope to achieve with AOG...';
      } else {
        // Hide all conditional groups
        toggleGroup('group-brand-name', false);
        toggleGroup('group-brand-website', false);
        toggleGroup('group-brand-query', false);
        toggleGroup('group-brand-budget', false);
        
        toggleGroup('group-creator-channel', false);
        toggleGroup('group-creator-query', false);
        toggleGroup('group-creator-link', false);
        toggleGroup('group-creator-subs', false);

        if (messageLabel) messageLabel.textContent = 'Your Message';
        if (messageInput) messageInput.placeholder = 'Tell us about your campaign...';
      }

      // 2. Discovery specify field
      const isDiscoveryOther = (discovery === 'Other');
      toggleGroup('group-discovery-other', isDiscoveryOther, isDiscoveryOther);
    };

    // ─── Email Format Authentication ───
    const emailInput = document.getElementById('email');
    const emailGroup = emailInput ? emailInput.closest('.form-group') : null;
    let emailErrorEl = null;

    if (emailGroup) {
      emailErrorEl = document.createElement('span');
      emailErrorEl.className = 'form-error-msg';
      emailErrorEl.style.display = 'none';
      emailGroup.appendChild(emailErrorEl);
    }

    const validateEmail = () => {
      if (!emailInput) return true;
      const value = emailInput.value.trim();
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      
      if (value === '') {
        emailInput.classList.remove('invalid');
        if (emailErrorEl) emailErrorEl.style.display = 'none';
        return false;
      }
      
      const isValid = emailRegex.test(value);
      if (isValid) {
        emailInput.classList.remove('invalid');
        if (emailErrorEl) {
          emailErrorEl.style.display = 'none';
          emailErrorEl.textContent = '';
        }
        return true;
      } else {
        emailInput.classList.add('invalid');
        if (emailErrorEl) {
          emailErrorEl.textContent = 'Please enter a valid email address (e.g. name@company.com)';
          emailErrorEl.style.display = 'block';
        }
        return false;
      }
    };

    if (emailInput) {
      emailInput.addEventListener('input', validateEmail);
      emailInput.addEventListener('blur', validateEmail);
    }

    // Capture invalid events to add styling class
    contactForm.addEventListener('invalid', (e) => {
      e.target.classList.add('invalid');
    }, true);

    // Remove invalid styling when field becomes valid
    contactForm.addEventListener('input', (e) => {
      if (e.target.classList.contains('invalid') && e.target.checkValidity()) {
        e.target.classList.remove('invalid');
      }
    }, true);

    contactForm.addEventListener('change', (e) => {
      if (e.target.classList.contains('invalid') && e.target.checkValidity()) {
        e.target.classList.remove('invalid');
      }
    }, true);

    // Attach selectors change listeners
    const selectors = ['userType', 'brandQueryType', 'creatorQueryType', 'discovery'];
    selectors.forEach(id => {
      const el = document.getElementById(id);
      if (el) el.addEventListener('change', updateFormFields);
    });

    // Initialize state
    updateFormFields();

    // Prevent submission with configuration placeholders or invalid email
    const SHEET_WEBHOOK_URL = 'https://script.google.com/macros/s/AKfycbw2K2bgwPlz1ZZcNhoowRYn2YN4dkE9gqGRABfEJQALZdnqoD64okgoBFn7p1EI2A_qRA/exec';

    // ── Submit-lock: prevents duplicate emails from rapid/double clicks ──
    let isSubmitting = false;
    const submitBtn = contactForm.querySelector('[type="submit"]');

    contactForm.addEventListener('submit', (e) => {
      // 1. Block if already in-flight
      if (isSubmitting) {
        e.preventDefault();
        return;
      }

      // 2. Validate email
      const isEmailValid = validateEmail();
      if (!isEmailValid) {
        e.preventDefault();
        if (emailInput) emailInput.focus();
        return;
      }

      // 3. Config placeholder guard
      const action = contactForm.getAttribute('action');
      if (action && action.includes('YOUR_FORM_ID')) {
        e.preventDefault();
        alert('Contact form is not configured yet. Please email us directly at partnerships@aogindia.com');
        return;
      }

      // 4. Lock the button immediately so rapid clicks are ignored
      isSubmitting = true;
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = "Sending\u2026 <i class='bx bx-loader-alt bx-spin'></i>";
      }

      // 5. Fire Google Sheets webhook (non-blocking, best-effort)
      const botcheck = contactForm.querySelector('[name="botcheck"]');
      if (!botcheck || !botcheck.checked) {
        fetch(SHEET_WEBHOOK_URL, {
          method: 'POST',
          body: new URLSearchParams(new FormData(contactForm)),
          keepalive: true
        }).catch(() => {});
      }

      // 6. Allow native web3forms POST to continue — it will navigate/redirect.
      //    If for any reason the page doesn't unload, re-enable after 8s as a fallback.
      setTimeout(() => {
        isSubmitting = false;
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = "Send Message <i class='bx bx-send'></i>";
        }
      }, 8000);
    });
  }
  
  // ─── Fetch Creator Stats ──────────────
  const fetchStats = async () => {
    try {
      const response = await fetch('js/data/stats.json');
      if (!response.ok) throw new Error('Stats not found');
      const data = await response.json();
      
      for (const [creatorKey, stats] of Object.entries(data)) {
        const ytEl = document.getElementById(`stat-yt-${creatorKey}`);
        const igEl = document.getElementById(`stat-ig-${creatorKey}`);
        
        if (ytEl && stats.youtube_subs) {
          ytEl.textContent = stats.youtube_subs;
        }
        if (igEl && stats.instagram_followers) {
          igEl.textContent = stats.instagram_followers;
        }
      }
    } catch (err) {
      console.warn('Could not load creator stats:', err);
    }
  };

  fetchStats();

});
