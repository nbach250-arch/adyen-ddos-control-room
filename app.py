"""Adyen-inspired classroom DDoS traffic control simulator (Python 3.9 compatible).
All traffic, providers and payments are synthetic. No external network operations.
"""
from flask import Flask, jsonify, render_template, request
from threading import RLock
import random
import time

app = Flask(__name__)
lock = RLock()
PROVIDERS = {
    'A': {'name': 'Shield A', 'capacity': 1300, 'latency': 72, 'cost': 0.9},
    'B': {'name': 'Shield B', 'capacity': 1650, 'latency': 92, 'cost': 1.35},
    'C': {'name': 'Shield C', 'capacity': 1050, 'latency': 58, 'cost': 1.1},
}
SCENARIOS = {
    'none': {'label': 'Normal traffic', 'attack': 0},
    'volumetric': {'label': 'Volumetric flood', 'attack': 1400},
    'burst': {'label': 'Sudden traffic spike', 'attack': 2300},
    'slowdown': {'label': 'Provider degradation', 'attack': 400},
    'multi': {'label': 'Multi-provider incident', 'attack': 1800},
}

def reset_state():
    return {
        'tick': 0, 'scenario': 'none', 'target': 'A', 'intensity': 70, 'legitimate': 550,
        'auto': True, 'filter': 75, 'reserve': 20, 'active': 'A',
        'fail_streak': 0, 'cooldown': 0, 'pause': False, 'total_success': 0,
        'total_failed': 0, 'total_blocked': 0, 'total_cost': 0.0, 'switches': 0,
        'events': [{'tick': 0, 'type': 'info', 'message': 'Control room online. Simulated payment traffic is flowing.'}],
        'history': [], 'providers': {}, 'last': {}, 'last_transition': None,
    }

state = reset_state()

def log(msg, kind='info'):
    state['events'].insert(0, {'tick': state['tick'], 'type': kind, 'message': msg})
    del state['events'][24:]

def simulation_step():
    if state['pause']:
        return
    state['tick'] += 1
    scenario = state['scenario']
    leg = state['legitimate']
    attack = int(SCENARIOS[scenario]['attack'] * state['intensity'] / 70.0)
    target = state['target']
    snapshot = {}
    for key, base in PROVIDERS.items():
        # Attacks do not magically disappear: filter effectiveness varies by provider.
        exposure = 1.0 if key == target else (0.68 if scenario == 'multi' else 0.09)
        if scenario == 'none':
            exposure = 0.0
        incoming_attack = attack * exposure
        base_effectiveness = min(0.97, state['filter'] / 100.0 + (0.04 if key == 'B' else 0))
        blocked = int(incoming_attack * base_effectiveness)
        leakage = max(0, int(incoming_attack) - blocked)
        if scenario == 'slowdown' and key == target:
            effective_cap = int(base['capacity'] * 0.44)
            extra_latency = 220
        else:
            effective_cap = base['capacity']
            extra_latency = 0
        safe_cap = int(effective_cap * (1.0 - state['reserve'] / 100.0))
        demand = leg + leakage
        # The provider must accommodate legitimate and unfiltered attack traffic.
        success_ratio = min(1.0, safe_cap / float(max(demand, 1)))
        latency = int(base['latency'] + extra_latency + max(0, demand / float(max(safe_cap, 1)) - 0.65) * 170 + random.randint(-6, 6))
        failed_fraction = max(0.0, 1 - success_ratio)
        snapshot[key] = {
            'id': key, 'name': base['name'], 'capacity': effective_cap, 'safe_capacity': safe_cap,
            'used': demand, 'utilization': round(100 * demand / float(max(effective_cap, 1))),
            'latency': latency, 'errors': round(failed_fraction * 100, 1),
            'blocked': blocked, 'leaked': leakage, 'healthy': success_ratio >= 0.95 and latency < 230,
            'cost_rate': base['cost'], 'success_ratio': success_ratio,
        }
    state['providers'] = snapshot
    current = snapshot[state['active']]
    if not current['healthy']:
        state['fail_streak'] += 1
    else:
        state['fail_streak'] = 0
    if state['cooldown'] > 0:
        state['cooldown'] -= 1
    # Switch after 3 unhealthy ticks; avoid thrashing via a short cooldown.
    if state['auto'] and state['fail_streak'] >= 3 and state['cooldown'] == 0:
        candidates = [p for p in snapshot.values() if p['id'] != state['active'] and p['healthy']]
        if candidates:
            # Choose stable backups with sufficient free capacity and low latency.
            best = min(candidates, key=lambda p: p['latency'] + p['utilization'] * 0.65)
            old = state['active']
            state['active'] = best['id']
            state['switches'] += 1
            state['fail_streak'] = 0
            state['cooldown'] = 5
            state['last_transition'] = {'from': old, 'to': best['id'], 'tick': state['tick']}
            log('AUTO FAILOVER: Shield %s → Shield %s; backup passed capacity and health checks.' % (old, best['id']), 'success')
        elif state['fail_streak'] == 3:
            log('NO SAFE BACKUP: Other providers also cannot meet health/capacity checks.', 'danger')
    chosen = snapshot[state['active']]
    succeeded = int(round(leg * chosen['success_ratio']))
    failed = leg - succeeded
    state['total_success'] += succeeded
    state['total_failed'] += failed
    state['total_blocked'] += chosen['blocked']
    state['total_cost'] += round((leg + chosen['leaked']) / 1000.0 * chosen['cost_rate'], 3)
    state['last'] = {'legitimate': leg, 'attack': attack, 'successful': succeeded,
                     'failed': failed, 'blocked': chosen['blocked'], 'latency': chosen['latency'],
                     'active': state['active']}
    state['history'].append({'tick': state['tick'], 'success': succeeded,
                             'failed': failed, 'latency': chosen['latency'],
                             'attack': attack, 'active': state['active']})
    del state['history'][:-75]
    if state['tick'] == 1:
        log('All three protection providers evaluated. Automatic routing is ready.')
    if state['tick'] % 12 == 0 and scenario != 'none':
        log('Attack telemetry updated: %s; target Shield %s.' % (SCENARIOS[scenario]['label'], target), 'warning')

def public_state():
    result = dict(state)
    result['scenarios'] = {k: v['label'] for k, v in SCENARIOS.items()}
    result['provider_info'] = PROVIDERS
    return result

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/state', methods=['GET'])
def get_state():
    with lock:
        return jsonify(public_state())

@app.route('/api/tick', methods=['POST'])
def tick():
    with lock:
        simulation_step()
        return jsonify(public_state())

@app.route('/api/action', methods=['POST'])
def action():
    global state
    data = request.get_json(silent=True) or {}
    command = data.get('command')
    with lock:
        if command == 'reset':
            state = reset_state()
            simulation_step()
        elif command == 'attack':
            scenario = data.get('scenario', 'volumetric')
            target = data.get('target', 'A')
            if scenario not in SCENARIOS or target not in PROVIDERS:
                return jsonify({'error': 'Invalid scenario or provider'}), 400
            state['scenario'] = scenario
            state['target'] = target
            state['fail_streak'] = 0
            log('SCENARIO: %s aimed at Shield %s.' % (SCENARIOS[scenario]['label'], target), 'warning' if scenario != 'none' else 'success')
        elif command == 'stop_attack':
            state['scenario'] = 'none'
            state['fail_streak'] = 0
            log('Attack stopped; providers recovering.', 'success')
        elif command == 'route':
            provider = data.get('provider')
            if provider not in PROVIDERS:
                return jsonify({'error': 'Unknown provider'}), 400
            if provider != state['active']:
                prior = state['active']
                state['active'] = provider
                state['fail_streak'] = 0
                state['cooldown'] = 4
                state['switches'] += 1
                state['last_transition'] = {'from': prior, 'to': provider, 'tick': state['tick']}
                log('MANUAL OVERRIDE: Route changed from Shield %s to Shield %s.' % (prior, provider), 'info')
        elif command == 'settings':
            for key, lo, hi in [('legitimate', 100, 1200), ('intensity', 10, 160), ('filter', 30, 95), ('reserve', 0, 40)]:
                if key in data:
                    try:
                        state[key] = max(lo, min(hi, int(data[key])))
                    except (ValueError, TypeError):
                        return jsonify({'error': 'Invalid setting'}), 400
            if 'auto' in data:
                state['auto'] = bool(data['auto'])
            if 'pause' in data:
                state['pause'] = bool(data['pause'])
        elif command == 'step':
            was_paused = state['pause']
            state['pause'] = False
            simulation_step()
            state['pause'] = was_paused
        else:
            return jsonify({'error': 'Unknown command'}), 400
        return jsonify(public_state())

if __name__ == '__main__':
    with lock:
        simulation_step()
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)
