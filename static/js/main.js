/**
 * RailSaathi Frontend JavaScript & Dynamic Helpers
 */

document.addEventListener('DOMContentLoaded', function() {
  // Initialize tooltips & popovers
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // Dynamic Fare Calculator for Book Coolie Form
  const bagsInput = document.getElementById('bagsInput');
  const baseFareElem = document.getElementById('displayBaseFare');
  const extraFareElem = document.getElementById('displayExtraFare');
  const totalFareElem = document.getElementById('displayTotalFare');

  function calculateFare() {
    if (!bagsInput || !totalFareElem) return;
    const bags = parseInt(bagsInput.value) || 1;
    const base = 100;
    const extraBags = Math.max(0, bags - 1);
    const extraFare = extraBags * 50;
    const total = base + extraFare;

    if (baseFareElem) baseFareElem.textContent = `₹${base}`;
    if (extraFareElem) extraFareElem.textContent = `₹${extraFare}`;
    if (totalFareElem) totalFareElem.textContent = `₹${total}`;
  }

  if (bagsInput) {
    bagsInput.addEventListener('input', calculateFare);
    bagsInput.addEventListener('change', calculateFare);
    calculateFare();
  }

  // Station selector dynamically updating platform list
  const stationSelect = document.getElementById('stationSelect');
  const platformSelect = document.getElementById('platformSelect');

  if (stationSelect && platformSelect) {
    stationSelect.addEventListener('change', function() {
      const stationId = this.value;
      if (!stationId) return;

      // Update URL param if on station list/booking page
      const currentUrl = new URL(window.location.href);
      const selectedOption = stationSelect.options[stationSelect.selectedIndex];
      const stationCode = selectedOption.getAttribute('data-code');
      if (stationCode) {
        currentUrl.searchParams.set('station', stationCode);
        // Only reload if user is switching station on coolie wizard to refresh coolie list
        if (window.location.pathname.includes('/bookings/book/')) {
          window.location.href = currentUrl.toString();
        }
      }
    });
  }

  // Auto-dismiss alerts after 6 seconds
  const autoAlerts = document.querySelectorAll('.alert-dismissible');
  autoAlerts.forEach(function(alert) {
    setTimeout(function() {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    }, 6000);
  });

  const assistantToggle = document.querySelector('.rs-assistant-toggle');
  const assistantPanel = document.querySelector('.rs-assistant-panel');
  const assistantClose = document.querySelector('.rs-assistant-close');
  const assistantForm = document.querySelector('.rs-assistant-form');
  const assistantMessages = document.querySelector('.rs-assistant-messages');

  function setAssistantOpen(isOpen) {
    if (!assistantPanel || !assistantToggle) return;
    assistantPanel.hidden = !isOpen;
    assistantToggle.setAttribute('aria-expanded', String(isOpen));
  }

  assistantToggle?.addEventListener('click', () => setAssistantOpen(assistantPanel.hidden));
  assistantClose?.addEventListener('click', () => setAssistantOpen(false));
  assistantForm?.addEventListener('submit', async function(event) {
    event.preventDefault();
    const input = assistantForm.querySelector('input[name="message"]');
    const message = input.value.trim();
    if (!message) return;
    assistantMessages.insertAdjacentHTML('beforeend', `<p class="assistant-bubble assistant-bubble-user"></p>`);
    assistantMessages.lastElementChild.textContent = message;
    input.value = '';
    const response = await fetch(assistantForm.action, {
      method: 'POST',
      headers: {'X-CSRFToken': assistantForm.querySelector('[name="csrfmiddlewaretoken"]').value},
      body: new URLSearchParams({message}),
    });
    const data = await response.json();
    const bubble = document.createElement('p');
    bubble.className = 'assistant-bubble assistant-bubble-bot';
    bubble.textContent = data.reply || data.error || 'Please try again.';
    assistantMessages.appendChild(bubble);
    assistantMessages.scrollTop = assistantMessages.scrollHeight;
  });

  // Live notification badge polling every 30 seconds
  const notifBadge = document.querySelector('.navbar .badge.bg-danger');
  const notifBell = document.querySelector('a[href*="notifications"] .badge');

  function pollNotifications() {
    fetch('/notifications/unread-count/')
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (!data) return;
        const count = data.unread_count;
        // Update all notification badges in navbar
        document.querySelectorAll('.notif-badge').forEach(function(badge) {
          if (count > 0) {
            badge.textContent = count;
            badge.style.display = '';
          } else {
            badge.style.display = 'none';
          }
        });
      })
      .catch(() => {});
  }

  // Only poll if user is logged in (bell icon exists)
  if (document.querySelector('.notif-badge')) {
    pollNotifications();
    setInterval(pollNotifications, 30000);
  }
});
