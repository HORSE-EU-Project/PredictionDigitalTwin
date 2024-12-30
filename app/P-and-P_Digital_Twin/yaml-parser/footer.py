
    print(f"\n*** Open5GS: Init 10 subscribers for UE container")
    o5gs   = Open5GS( "172.17.0.2" ,"27017")
    o5gs.removeAllSubscribers()
    with open( prj_folder + "/python_modules/subscriber_profile.json" , 'r') as f:
        profile = json.load( f )
    
    counter = 894
    for _ in range(10):
        counter += 1
        prefix = "001011234567"
        prefix += str(counter)
        profile["imsi"] = prefix
        o5gs.addSubscriber(profile)

    info("\n*** Starting network\n")
    net.start()

    # Fork between CLI and RESTAPI
    processid = os.fork()
    print (" Process ID: " + str(processid))

    if processid >0: # Main process
        mininet_rest = MininetRest(net)
        mininet_rest.run()
        print('INFO:     Main waiting for childs to terminate...')
        time.sleep(2)
        # get all active child processes
        active = active_children()
        # terminate all active children
        for child in active:
            child.kill()
        # block until all children have closed
        for child in active:
            child.join()
        # report active children
        active = active_children()
        print(f'INFO:    Active Children: {len(active)}')
    else:
        time.sleep(2)
        if not AUTOTEST_MODE:
            CLI(net)
        net.stop()
        print("\n*** CTRL+C to terminate\n")