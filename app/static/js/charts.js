/**
 * Skrypty do obsługi wykresów w aplikacji eBOK
 */

// Inicjalizacja wykresu trendów zużycia mediów
function initConsumptionChart(chartData) {
  const ctx = document.getElementById('consumptionChart').getContext('2d');

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: chartData.periods,
      datasets: [
        {
          label: 'Prąd (kWh)',
          data: chartData.electricity,
          borderColor: 'rgba(0, 123, 255, 1)',
          backgroundColor: 'rgba(0, 123, 255, 0.1)',
          tension: 0.4,
          fill: true
        },
        {
          label: 'Woda (m³)',
          data: chartData.water,
          borderColor: 'rgba(23, 162, 184, 1)',
          backgroundColor: 'rgba(23, 162, 184, 0.1)',
          tension: 0.4,
          fill: true
        },
        {
          label: 'Gaz (m³)',
          data: chartData.gas,
          borderColor: 'rgba(255, 193, 7, 1)',
          backgroundColor: 'rgba(255, 193, 7, 0.1)',
          tension: 0.4,
          fill: true
        },
        {
          label: 'Ogrzewanie (GJ)',
          data: chartData.heating,
          borderColor: 'rgba(220, 53, 69, 1)',
          backgroundColor: 'rgba(220, 53, 69, 0.1)',
          tension: 0.4,
          fill: true
        }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: 'top',
        },
        title: {
          display: false,
        },
        tooltip: {
          mode: 'index',
          intersect: false,
          callbacks: {
            label: function(context) {
              let label = context.dataset.label || '';
              if (label) {
                label += ': ';
              }
              if (context.parsed.y !== null) {
                label += context.parsed.y.toFixed(2);
              }
              return label;
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  });
}

// Inicjalizacja wykresu anomalii dla alertów
function initAnomalyChart(chartElement, data) {
  const ctx = document.getElementById(chartElement).getContext('2d');

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.labels,
      datasets: [
        {
          label: 'Wartość rzeczywista',
          data: data.actual,
          backgroundColor: 'rgba(75, 192, 192, 0.5)',
          borderColor: 'rgba(75, 192, 192, 1)',
          borderWidth: 1
        },
        {
          label: 'Wartość oczekiwana',
          data: data.expected,
          backgroundColor: 'rgba(54, 162, 235, 0.5)',
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 1
        }
      ]
    },
    options: {
      responsive: true,
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  });
}

// Inicjalizacja wykresu efektywności budynku
function initEfficiencyChart(score) {
  const ctx = document.getElementById('efficiencyChart').getContext('2d');

  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Efektywność', 'Potencjał poprawy'],
      datasets: [{
        data: [score, 100 - score],
        backgroundColor: [
          score > 75 ? 'rgba(40, 167, 69, 0.7)' : 
            score > 50 ? 'rgba(255, 193, 7, 0.7)' : 'rgba(220, 53, 69, 0.7)',
          'rgba(200, 200, 200, 0.2)'
        ],
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      cutout: '75%',
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          enabled: false
        }
      }
    }
  });
}
