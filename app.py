from flask import Flask, request, jsonify
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Helper function to calculate metrics
def calculate_metrics(processes, execution_order):
    n = len(processes)
    waiting_time = [0] * n
    turnaround_time = [0] * n
    completion_time = [0] * n
    
    # Calculate completion times
    for exec in execution_order:
        pid = exec['pid']
        idx = processes.index(next(p for p in processes if p['pid'] == pid))
        completion_time[idx] = exec['end']
    
    # Calculate waiting and turnaround times
    for i, proc in enumerate(processes):
        turnaround_time[i] = completion_time[i] - proc['arrival']
        waiting_time[i] = turnaround_time[i] - proc['burst']
    
    return {
        'waiting_time': waiting_time,
        'turnaround_time': turnaround_time,
        'avg_waiting_time': sum(waiting_time) / n,
        'avg_turnaround_time': sum(turnaround_time) / n,
        'total_time': max(completion_time) if completion_time else 0
    }

@app.route('/simulate', methods=['POST'])
def simulate():
    data = request.json
    algorithm = data['algorithm']
    pids = data['pids']
    arrival = data['arrival']
    burst = data['burst']
    
    processes = [{
        'pid': pid,
        'arrival': arr,
        'burst': bur
    } for pid, arr, bur in zip(pids, arrival, burst)]
    
    if algorithm == 'fcfs':
        return simulate_fcfs(processes)
    elif algorithm == 'sjf':
        return simulate_sjf(processes)
    elif algorithm == 'priority':
        priority = data['priority']
        return simulate_priority(processes, priority)
    elif algorithm == 'rr':
        quantum = data['quantum']
        return simulate_rr(processes, quantum)
    else:
        return jsonify({'error': 'Invalid algorithm'}), 400

def simulate_fcfs(processes):
    # Sort by arrival time
    processes.sort(key=lambda x: x['arrival'])
    
    execution_order = []
    current_time = 0
    
    for proc in processes:
        start = max(current_time, proc['arrival'])
        end = start + proc['burst']
        execution_order.append({
            'pid': proc['pid'],
            'start': start,
            'end': end,
            'duration': proc['burst']
        })
        current_time = end
    
    metrics = calculate_metrics(processes, execution_order)
    
    return jsonify({
        'processes': processes,
        'execution_order': execution_order,
        'gantt': execution_order,
        **metrics
    })

def simulate_sjf(processes):
    processes = processes.copy()
    execution_order = []
    current_time = 0
    completed = 0
    n = len(processes)
    
    while completed < n:
        # Get arrived and not completed processes
        available = [p for p in processes 
                    if p['arrival'] <= current_time and 'completed' not in p]
        
        if not available:
            current_time += 1
            continue
        
        # Get shortest job
        current = min(available, key=lambda x: x['burst'])
        start = current_time
        end = start + current['burst']
        
        execution_order.append({
            'pid': current['pid'],
            'start': start,
            'end': end,
            'duration': current['burst']
        })
        
        current_time = end
        current['completed'] = True
        completed += 1
    
    metrics = calculate_metrics(processes, execution_order)
    
    return jsonify({
        'processes': processes,
        'execution_order': execution_order,
        'gantt': execution_order,
        **metrics
    })

def simulate_priority(processes, priorities):
    processes = [dict(p, priority=pri) for p, pri in zip(processes, priorities)]
    execution_order = []
    current_time = 0
    completed = 0
    n = len(processes)
    
    while completed < n:
        # Get arrived and not completed processes
        available = [p for p in processes 
                    if p['arrival'] <= current_time and 'completed' not in p]
        
        if not available:
            current_time += 1
            continue
        
        # Get highest priority (lower number = higher priority)
        current = min(available, key=lambda x: x['priority'])
        start = current_time
        end = start + current['burst']
        
        execution_order.append({
            'pid': current['pid'],
            'start': start,
            'end': end,
            'duration': current['burst']
        })
        
        current_time = end
        current['completed'] = True
        completed += 1
    
    metrics = calculate_metrics(processes, execution_order)
    
    return jsonify({
        'processes': processes,
        'execution_order': execution_order,
        'gantt': execution_order,
        **metrics
    })

def simulate_rr(processes, quantum):
    processes = [dict(p, remaining=p['burst']) for p in processes]
    execution_order = []
    queue = []
    current_time = 0
    idle_time = 0
    
    # Initial queue population
    for p in processes:
        if p['arrival'] == 0:
            queue.append(p)
    
    while True:
        if not queue:
            # Check if all processes are done
            if all('completed' in p for p in processes):
                break
            
            # No processes ready, advance time
            current_time += 1
            idle_time += 1
            
            # Check for new arrivals
            for p in processes:
                if p['arrival'] == current_time and p not in queue and 'completed' not in p:
                    queue.append(p)
            continue
        
        current = queue.pop(0)
        time_slice = min(quantum, current['remaining'])
        
        execution_order.append({
            'pid': current['pid'],
            'start': current_time,
            'end': current_time + time_slice,
            'duration': time_slice
        })
        
        current_time += time_slice
        current['remaining'] -= time_slice
        
        # Check for new arrivals during this time slice
        for p in processes:
            if (p['arrival'] > current_time - time_slice and 
                p['arrival'] <= current_time and 
                p not in queue and 
                'completed' not in p):
                queue.append(p)
        
        if current['remaining'] == 0:
            current['completed'] = True
        else:
            queue.append(current)
    
    metrics = calculate_metrics(processes, execution_order)
    metrics['idle_time'] = idle_time
    
    return jsonify({
        'processes': [{k: v for k, v in p.items() if k != 'remaining'} for p in processes],
        'execution_order': execution_order,
        'gantt': execution_order,
        **metrics
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)