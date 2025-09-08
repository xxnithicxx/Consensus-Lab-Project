#!/usr/bin/env python3
"""
Blockchain Log Analysis Script (CLI Only)
Analyzes logs from a 5-node blockchain simulation and creates text-based visualizations
"""

import os
import re
from datetime import datetime
from collections import defaultdict

def parse_log_file(filepath):
    """Parse a single log file and extract blockchain states and events"""
    states = []
    events = []
    node_id = re.search(r'node_(\d+)', filepath).group(1)
    
    with open(filepath, 'r') as f:
        for line in f:
            # Parse timestamp
            timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})', line)
            if not timestamp_match:
                continue
                
            timestamp_str = timestamp_match.group(1)
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
            
            # Parse blockchain state
            if 'Blockchain state:' in line:
                state_match = re.search(r"Blockchain state: ({.*})", line)
                if state_match:
                    try:
                        state_dict = eval(state_match.group(1))
                        state_dict['timestamp'] = timestamp
                        state_dict['node_id'] = node_id
                        states.append(state_dict)
                    except:
                        pass
            
            # Parse events
            if 'EVENT:' in line:
                event_match = re.search(r"EVENT: ({.*})", line)
                if event_match:
                    try:
                        event_dict = eval(event_match.group(1))
                        event_dict['log_timestamp'] = timestamp
                        events.append(event_dict)
                    except:
                        pass
    
    return states, events

def analyze_logs():
    """Analyze all log files in the logs directory"""
    log_dir = '/home/nico/workspace/Consensus/logs'
    all_states = []
    all_events = []
    
    # Process each log file
    for filename in sorted(os.listdir(log_dir)):
        if filename.startswith('node_') and filename.endswith('.log'):
            filepath = os.path.join(log_dir, filename)
            states, events = parse_log_file(filepath)
            all_states.extend(states)
            all_events.extend(events)
    
    return all_states, all_events

def create_transaction_flow_table(events):
    """Create transaction flow matrix as text table"""
    # Initialize flow matrix
    flow_matrix = defaultdict(lambda: defaultdict(float))
    count_matrix = defaultdict(lambda: defaultdict(int))
    
    for event in events:
        if event['event_type'] == 'transaction_broadcast':
            sender = int(event['node_id'])
            receiver = int(event['data']['receiver'])
            amount = event['data']['amount']
            flow_matrix[sender][receiver] += amount
            count_matrix[sender][receiver] += 1
    
    print("\n" + "="*80)
    print("💰 TRANSACTION FLOW MATRIX (Total Amount)")
    print("="*80)
    
    # Header
    print(f"{'From\\To':<8}", end="")
    for j in range(5):
        print(f"{'Node '+str(j):>12}", end="")
    print(f"{'Total Sent':>12}")
    print("-" * 80)
    
    # Rows
    for i in range(5):
        print(f"Node {i:<3}", end="")
        row_total = 0
        for j in range(5):
            amount = flow_matrix[i][j]
            if amount > 0:
                print(f"{amount:>12.2f}", end="")
                row_total += amount
            else:
                print(f"{'0.00':>12}", end="")
        print(f"{row_total:>12.2f}")
    
    # Column totals
    print("-" * 80)
    print(f"{'Total Recv':<8}", end="")
    for j in range(5):
        col_total = sum(flow_matrix[i][j] for i in range(5))
        print(f"{col_total:>12.2f}", end="")
    grand_total = sum(sum(flow_matrix[i][j] for j in range(5)) for i in range(5))
    print(f"{grand_total:>12.2f}")
    
    print("\n" + "="*80)
    print("📊 TRANSACTION COUNT MATRIX")
    print("="*80)
    
    # Header
    print(f"{'From\\To':<8}", end="")
    for j in range(5):
        print(f"{'Node '+str(j):>12}", end="")
    print(f"{'Total Sent':>12}")
    print("-" * 80)
    
    # Rows
    for i in range(5):
        print(f"Node {i:<3}", end="")
        row_total = 0
        for j in range(5):
            count = count_matrix[i][j]
            print(f"{count:>12}", end="")
            row_total += count
        print(f"{row_total:>12}")
    
    # Column totals
    print("-" * 80)
    print(f"{'Total Recv':<8}", end="")
    for j in range(5):
        col_total = sum(count_matrix[i][j] for i in range(5))
        print(f"{col_total:>12}", end="")
    grand_total = sum(sum(count_matrix[i][j] for j in range(5)) for i in range(5))
    print(f"{grand_total:>12}")

def create_activity_table(events):
    """Create transaction activity table"""
    print("\n" + "="*80)
    print("📈 TRANSACTION ACTIVITY SUMMARY")
    print("="*80)
    
    # Calculate activity per node
    activity_data = {}
    for node_id in range(5):
        broadcasts = [e for e in events if e['event_type'] == 'transaction_broadcast' and e['node_id'] == str(node_id)]
        receives = [e for e in events if e['event_type'] == 'transaction_received' and e['node_id'] == str(node_id)]
        
        sent_amount = sum([e['data']['amount'] for e in broadcasts])
        received_amount = sum([e['data']['amount'] for e in receives])
        
        activity_data[node_id] = {
            'sent_count': len(broadcasts),
            'sent_amount': sent_amount,
            'received_count': len(receives),
            'received_amount': received_amount
        }
    
    # Table header
    print(f"{'Node':<6}{'Sent Count':>12}{'Sent Amount':>15}{'Recv Count':>12}{'Recv Amount':>15}{'Net Amount':>15}")
    print("-" * 80)
    
    # Table rows
    for node_id in range(5):
        data = activity_data[node_id]
        net_amount = data['received_amount'] - data['sent_amount']
        print(f"{node_id:<6}{data['sent_count']:>12}{data['sent_amount']:>15.2f}"
              f"{data['received_count']:>12}{data['received_amount']:>15.2f}{net_amount:>15.2f}")
    
    # Totals
    print("-" * 80)
    total_sent_count = sum(data['sent_count'] for data in activity_data.values())
    total_sent_amount = sum(data['sent_amount'] for data in activity_data.values())
    total_recv_count = sum(data['received_count'] for data in activity_data.values())
    total_recv_amount = sum(data['received_amount'] for data in activity_data.values())
    
    print(f"{'Total':<6}{total_sent_count:>12}{total_sent_amount:>15.2f}"
          f"{total_recv_count:>12}{total_recv_amount:>15.2f}{0.0:>15.2f}")

def print_blockchain_states(states):
    """Print blockchain states table"""
    print("\n" + "="*80)
    print("🔗 BLOCKCHAIN STATES SUMMARY")
    print("="*80)
    
    # Get unique node IDs
    node_ids = sorted(set(state['node_id'] for state in states))
    
    # Get final state for each node
    final_states = {}
    for state in states:
        node_id = state['node_id']
        if node_id not in final_states or state['timestamp'] > final_states[node_id]['timestamp']:
            final_states[node_id] = state
    
    # Print table header
    print(f"{'Node':<6}{'Chain Len':>10}{'Block Height':>12}{'Balance':>10}{'Pending':>8}{'Genesis Hash':<20}")
    print("-" * 80)
    
    # Print each node's final state
    for node_id in node_ids:
        state = final_states[node_id]
        genesis_hash = state['latest_block_hash'][:16] + "..."
        print(f"{node_id:<6}{state['chain_length']:>10}{state['latest_block_height']:>12}"
              f"{state['balance']:>10}{state['pending_transactions']:>8}{genesis_hash:<20}")

def print_basic_stats(states, events):
    """Print basic simulation statistics"""
    print("="*80)
    print("🔗 BLOCKCHAIN SIMULATION LOG ANALYSIS (CLI)")
    print("="*80)
    
    node_count = len(set(state['node_id'] for state in states))
    total_transactions = len([e for e in events if e['event_type'] == 'transaction_broadcast'])
    total_amount = sum([e['data']['amount'] for e in events if e['event_type'] == 'transaction_broadcast'])
    
    print(f"\n📊 SIMULATION OVERVIEW:")
    print(f"   • Total Nodes: {node_count}")
    print(f"   • Consensus: Proof of Work (PoW)")
    print(f"   • Scenario: Delays with seed 42")
    print(f"   • Duration: ~30 seconds")
    print(f"   • Total Transactions: {total_transactions}")
    print(f"   • Total Volume: {total_amount:.2f}")
    print(f"   • Average Amount: {total_amount/total_transactions:.2f}")
    
    # Transaction frequency analysis
    transaction_times = []
    for event in events:
        if event['event_type'] == 'transaction_broadcast':
            transaction_times.append(event['timestamp'])
    
    if len(transaction_times) > 1:
        intervals = [transaction_times[i] - transaction_times[i-1] for i in range(1, len(transaction_times))]
        avg_interval = sum(intervals) / len(intervals)
        print(f"   • Avg time between transactions: {avg_interval:.2f} seconds")
        print(f"   • Transaction frequency: {1/avg_interval:.2f} tx/second")

def main():
    """Main function to run the CLI analysis"""
    print("🔍 Analyzing blockchain simulation logs...")
    
    # Parse all log files
    states, events = analyze_logs()
    print(f"📊 Parsed {len(states)} blockchain states and {len(events)} events")
    
    # Print basic statistics
    print_basic_stats(states, events)
    
    # Print blockchain states table
    print_blockchain_states(states)
    
    # Print transaction activity table
    create_activity_table(events)
    
    # Print transaction flow matrices
    create_transaction_flow_table(events)
    
    print("\n" + "="*80)
    print("✅ CLI Analysis Complete!")
    print("="*80)

if __name__ == "__main__":
    main()
