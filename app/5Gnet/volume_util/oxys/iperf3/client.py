import iperf3

client = iperf3.Client()
# client.server_hostname = '127.0.0.1'
client.server_hostname = '172.17.0.3'
client.port = 6969
client.duration = 1
client.protocol = 'udp'
client.json_output = True
client.blksize = 9000
result = client.run()

if result.error:
    print(result.error)
else:
    print('')
    print('Test completed:')
    print('  started at         {0}'.format(result.time))
    print('  bytes transmitted  {0}'.format(result.bytes))
    print('  jitter (ms)        {0}'.format(result.jitter_ms))
    print('  avg cpu load       {0}%\n'.format(result.local_cpu_total))

    print('Average transmitted data in all sorts of networky formats:')
    print('  bits per second      (bps)   {0}'.format(result.bps))
    print('  Kilobits per second  (kbps)  {0}'.format(result.kbps))
    print('  Megabits per second  (Mbps)  {0}'.format(result.Mbps))
    print('  KiloBytes per second (kB/s)  {0}'.format(result.kB_s))
    print('  MegaBytes per second (MB/s)  {0}'.format(result.MB_s))
