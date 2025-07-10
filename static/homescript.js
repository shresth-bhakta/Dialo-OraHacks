// Smooth scroll to contact section
document.getElementById('contact-link').addEventListener('click', function (event) {
    event.preventDefault();
    document.getElementById('contact-details').scrollIntoView({ behavior: 'smooth' });
  });
  
  // Dark mode toggle
  const toggle = document.getElementById('toggle-dark');
  toggle.addEventListener('click', () => {
    document.body.classList.toggle('dark-mode');
    toggle.classList.add("fade");
    setTimeout(() => {
      toggle.textContent = document.body.classList.contains('dark-mode') ? '☀️' : '🌙';
      toggle.classList.remove("fade");
    }, 200);
  });
  
  // Info tab toggle
  const infoTab = document.getElementById('info-tab');
  const infoModal = document.getElementById('info-modal');
  const closeInfo = document.getElementById('close-info');
  
  infoTab.addEventListener('click', (e) => {
    e.preventDefault();
    infoModal.style.display = 'flex';
  });
  
  closeInfo.addEventListener('click', () => {
    infoModal.style.display = 'none';
  });
  
  window.addEventListener('click', (e) => {
    if (e.target === infoModal) {
      infoModal.style.display = 'none';
    }
  });
  
  // Toggle contact form
  const toggleBtn = document.getElementById('toggle-form-btn');
  const contactFormContainer = document.getElementById('contact-form-container');
  
  toggleBtn.addEventListener('click', () => {
    contactFormContainer.classList.toggle('show');
    toggleBtn.textContent = contactFormContainer.classList.contains('show')
      ? '❌ Close Message Form'
      : '📩 Open Message Form';
  });
  
  // Floating message button logic
  const messageFab = document.getElementById('message-fab');
  const messageModal = document.getElementById('message-modal');
  const closeMessage = document.getElementById('close-message');
  
  messageFab.addEventListener('click', () => {
    messageModal.style.display = 'flex';
  });
  
  closeMessage.addEventListener('click', () => {
    messageModal.style.display = 'none';
  });
  
  window.addEventListener('click', (e) => {
    if (e.target === messageModal) {
      messageModal.style.display = 'none';
    }
  });
  
  // Optional form submission
  document.getElementById('contact-form-floating').addEventListener('submit', function (e) {
    e.preventDefault();
    alert('Thanks for your message!');
    messageModal.style.display = 'none';
  });
  