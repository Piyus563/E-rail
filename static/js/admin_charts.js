/**
 * RailSaathi Admin Analytics & Chart.js Visualizations
 */

document.addEventListener('DOMContentLoaded', function() {
  const chartCanvas1 = document.getElementById('dailyBookingsChart');
  const chartCanvas2 = document.getElementById('bookingStatusChart');
  const chartCanvas3 = document.getElementById('assistanceTypesChart');
  const chartCanvas4 = document.getElementById('stationDemandChart');

  if (!chartCanvas1 && !chartCanvas2) return;

  fetch('/portal/api/charts-data/')
    .then(response => response.json())
    .then(data => {
      // 1. Daily Bookings Chart
      if (chartCanvas1) {
        new Chart(chartCanvas1, {
          type: 'line',
          data: {
            labels: data.daily_bookings.labels,
            datasets: [{
              label: 'Bookings',
              data: data.daily_bookings.data,
              borderColor: '#2563eb',
              backgroundColor: 'rgba(37, 99, 235, 0.1)',
              borderWidth: 3,
              fill: true,
              tension: 0.35,
              pointBackgroundColor: '#2563eb',
              pointRadius: 5
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false }
            },
            scales: {
              y: {
                beginAtZero: true,
                ticks: { stepSize: 1 }
              }
            }
          }
        });
      }

      // 2. Booking Status Breakdown
      if (chartCanvas2) {
        new Chart(chartCanvas2, {
          type: 'doughnut',
          data: {
            labels: data.booking_status.labels,
            datasets: [{
              data: data.booking_status.data,
              backgroundColor: [
                '#f59e0b', // Requested
                '#2563eb', // Accepted
                '#8b5cf6', // Service Started
                '#10b981', // Completed
                '#ef4444'  // Cancelled
              ],
              borderWidth: 2
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { position: 'bottom' }
            },
            cutout: '70%'
          }
        });
      }

      // 3. Assistance Types Chart
      if (chartCanvas3) {
        new Chart(chartCanvas3, {
          type: 'bar',
          data: {
            labels: data.assistance_types.labels,
            datasets: [{
              label: 'Assistance Requests',
              data: data.assistance_types.data,
              backgroundColor: '#0ea5e9',
              borderRadius: 8
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false }
            },
            scales: {
              y: { beginAtZero: true, ticks: { stepSize: 1 } }
            }
          }
        });
      }

      // 4. Station Demand Chart
      if (chartCanvas4) {
        new Chart(chartCanvas4, {
          type: 'bar',
          data: {
            labels: data.station_demand.labels,
            datasets: [{
              label: 'Demand by Station',
              data: data.station_demand.data,
              backgroundColor: '#0f2b48',
              borderRadius: 8
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false }
            },
            scales: {
              y: { beginAtZero: true, ticks: { stepSize: 1 } }
            }
          }
        });
      }
    })
    .catch(err => console.error("Error loading analytics data:", err));
});
