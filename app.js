const processList = [];

function addProcess() {
  const pid = document.getElementById("pid").value;
  const arrival = parseInt(document.getElementById("arrival").value);
  const burst = parseInt(document.getElementById("burst").value);
  const priority = parseInt(document.getElementById("priority").value || 0);

  if (!pid || isNaN(arrival) || isNaN(burst)) {
    alert("Please fill PID, Arrival, and Burst Time");
    return;
  }

  processList.push({ pid, arrival, burst, priority });

  document.getElementById("processTable").innerHTML = processList
    .map(
      (p) => `
      <tr>
        <td>${p.pid}</td>
        <td>${p.arrival}</td>
        <td>${p.burst}</td>
        <td>${p.priority}</td>
      </tr>
    `
    )
    .join("");

  // Reset form
  document.getElementById("pid").value = "";
  document.getElementById("arrival").value = "";
  document.getElementById("burst").value = "";
  document.getElementById("priority").value = "";
}

function runSimulation() {
  const algo = document.querySelector('input[name="algorithm"]:checked').value;
  console.log("Running:", algo, processList);

  // Placeholder for backend connection
  fetch("http://localhost:3000/simulate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ algorithm: algo, processes: processList }),
  })
    .then((res) => res.json())
    .then((data) => {
      const output = document.getElementById("output");
      output.innerHTML = `
        <div class="bg-gray-800 p-4 rounded">
          <h3 class="text-lg font-semibold mb-2">Simulation Result</h3>
          <pre>${JSON.stringify(data, null, 2)}</pre>
        </div>
      `;
    })
    .catch((err) => {
      alert("Failed to fetch result.");
      console.error(err);
    });
}
