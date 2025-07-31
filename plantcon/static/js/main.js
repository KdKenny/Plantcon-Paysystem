const date = new Date();
document.querySelector('.year').innerHTML = date.getFullYear();

// Custom Navbar Toggle Implementation
document.addEventListener('DOMContentLoaded', function() {
  initializeNavbar();
});

function initializeNavbar() {
  const toggler = document.getElementById('navbarToggler');
  const menu = document.getElementById('navbarMenu');
  
  if (!toggler || !menu) {
    console.warn('Navbar elements not found');
    return;
  }
  
  // Debug: Check if hamburger lines exist
  const hamburgerLines = toggler.querySelectorAll('.hamburger-line');
  console.log('Found hamburger lines:', hamburgerLines.length);

  // Initialize state
  let isMenuOpen = false;
  
  // Set initial state
  updateMenuVisibility();
  
  // Toggle button click handler
  toggler.addEventListener('click', function(e) {
    e.preventDefault();
    e.stopPropagation();
    
    isMenuOpen = !isMenuOpen;
    updateMenuVisibility();
    
    // Update aria-expanded for accessibility
    toggler.setAttribute('aria-expanded', isMenuOpen.toString());
  });
  
  // Close menu when clicking outside
  document.addEventListener('click', function(e) {
    if (isMenuOpen && !toggler.contains(e.target) && !menu.contains(e.target)) {
      isMenuOpen = false;
      updateMenuVisibility();
      toggler.setAttribute('aria-expanded', 'false');
    }
  });
  
  // Close menu when window is resized to desktop view
  window.addEventListener('resize', function() {
    if (window.innerWidth >= 992) { // Bootstrap lg breakpoint
      isMenuOpen = false;
      updateMenuVisibility();
      toggler.setAttribute('aria-expanded', 'false');
    }
  });
  
  // Close menu when nav links are clicked (mobile only)
  const navLinks = menu.querySelectorAll('.nav-link');
  navLinks.forEach(link => {
    link.addEventListener('click', function() {
      if (window.innerWidth < 992) {
        isMenuOpen = false;
        updateMenuVisibility();
        toggler.setAttribute('aria-expanded', 'false');
      }
    });
  });
  
  function updateMenuVisibility() {
    if (isMenuOpen) {
      menu.classList.add('show');
      menu.classList.remove('collapse');
      toggler.classList.add('active');
    } else {
      menu.classList.remove('show');
      menu.classList.add('collapse');
      toggler.classList.remove('active');
    }
  }
}

// Fade out messages
setTimeout(() => {
  const messageElement = document.getElementById('message');
  if (messageElement && typeof $ !== 'undefined') {
    $("#message").fadeOut("slow");
  }
}, 3000);