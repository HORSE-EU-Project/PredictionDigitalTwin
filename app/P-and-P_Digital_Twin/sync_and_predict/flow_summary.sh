tshark -r $1 -T fields \
-e ip.src -e ip.dst -e _ws.col.Protocol -e frame.len \
-E separator=, \
| sort \
| awk -F',' '
BEGIN {
    # Print the header first
    print "ipsrc,ipdst,protocol,throughput,total_packets";
}
{
    # $1=ip.src, $2=ip.dst, $3=protocol, $4=frame.len (bytes)

    # 1. Create a CANONICAL key: IP_A and IP_B are always ordered lexicographically.
    # This ensures A->B and B->A packets aggregate into a single flow count.
    if ($1 < $2) {
        IP_A = $1;
        IP_B = $2;
    } else {
        IP_A = $2;
        IP_B = $1;
    }
    
    # The unique key for the flow is IP_A, IP_B, Protocol
    key = IP_A "," IP_B "," $3;

    # 2. Accumulate bytes (frame.len, $4) and packets (count)
    flows_bytes[key] += $4;
    flows_pkts[key]++;
    
    # 3. Store the canonical key for later printing
    if (! (key in keys_array)) {
        keys_array[key] = key;
    }
}
END {
    # Print the final aggregated results
    for (key in keys_array) {
        # 'key' already contains IP_A,IP_B,Protocol
        print key "," flows_bytes[key] "," flows_pkts[key];
    }
}' > aggregated_flow_summary.csv
