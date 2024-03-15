Partendo da zero bisogna:
- Creare le immagini per open5gs e ueransim:
$ cd build_images
$ ./build.sh
- Creare l'immagine per oxys-reflector (questo l'ho lasciato nella cartella oxys)
$ cd volume_util/oxys/
$ ./build_image.sh

- Creare scenario e far girare test (ci sono le indicazioni nel file Test_oxys.py)
$ ./clean.sh
$ sudo python3 net_deploy.py scenarios/oxys.json
$ python3 Test_oxys.py
